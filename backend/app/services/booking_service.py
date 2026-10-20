"""Booking use-cases: slot lookup, create, cancel, reschedule."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.config import Settings
from app.core.errors import (
    NotFoundError,
    SlotUnavailableError,
    StaleVersionError,
    ValidationError,
)
from app.core.time import to_utc, tz, utcnow
from app.db.models import Booking, BookingStatus, Doctor, Patient
from app.domain.policies import BookingPolicy
from app.domain.slots import Slot, find_slot, generate_slots
from app.services.notifications import Notifier, get_notifier

log = logging.getLogger("booking")


class BookingService:
    def __init__(self, db: Session, settings: Settings, notifier: Notifier | None = None) -> None:
        self.db = db
        self.settings = settings
        self.tz = tz(settings.clinic_timezone)
        self.notifier = notifier or get_notifier()
        self.policy = BookingPolicy(
            cancel_min_hours_before=settings.cancel_min_hours_before,
            reschedule_min_hours_before=settings.reschedule_min_hours_before,
            max_reschedules=settings.max_reschedules,
        )

    # ---- lookups -------------------------------------------------------------------
    def get_doctor(self, doctor_id: int) -> Doctor:
        doctor = self.db.get(Doctor, doctor_id)
        if doctor is None or not doctor.is_active:
            raise NotFoundError(f"doctor {doctor_id} not found")
        return doctor

    def get_booking(self, booking_id: int) -> Booking:
        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError(f"booking {booking_id} not found")
        return booking

    def booked_starts(self, doctor_id: int, date_from: date, date_to: date) -> set[datetime]:
        start = datetime.combine(date_from, datetime.min.time(), tzinfo=self.tz)
        end = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=self.tz)
        rows = self.db.scalars(
            select(Booking.slot_start).where(
                Booking.doctor_id == doctor_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.slot_start >= to_utc(start),
                Booking.slot_start < to_utc(end),
            )
        ).all()
        return {to_utc(r) for r in rows}

    def slots_for(
        self, doctor: Doctor, date_from: date, date_to: date, now: datetime | None = None
    ) -> list[Slot]:
        now = now or utcnow()
        today = now.astimezone(self.tz).date()
        max_day = today + timedelta(days=self.settings.booking_max_days_ahead)
        if date_to > max_day:
            raise ValidationError(f"slots can only be viewed up to {max_day.isoformat()}")
        if (date_to - date_from).days > 31:
            raise ValidationError("date range must be 31 days or fewer")
        return generate_slots(
            templates=list(doctor.templates),
            exceptions=list(doctor.exceptions),
            booked_starts_utc=self.booked_starts(doctor.id, date_from, date_to),
            slot_minutes=doctor.slot_minutes,
            date_from=date_from,
            date_to=date_to,
            tzinfo=self.tz,
            now=now,
            min_lead=timedelta(minutes=self.settings.booking_min_lead_minutes),
        )

    def _resolve_slot(self, doctor: Doctor, slot_start: datetime, now: datetime) -> Slot:
        local_day = to_utc(slot_start).astimezone(self.tz).date()
        slots = self.slots_for(doctor, local_day, local_day, now=now)
        slot = find_slot(slots, slot_start)
        if slot is None:
            raise SlotUnavailableError("requested time is not a bookable slot for this doctor")
        if not slot.available:
            raise SlotUnavailableError("slot already booked")
        return slot

    # ---- commands ------------------------------------------------------------------
    def create(
        self,
        *,
        doctor_id: int,
        patient: Patient,
        slot_start: datetime,
        note: str | None = None,
        now: datetime | None = None,
    ) -> Booking:
        now = now or utcnow()
        doctor = self.get_doctor(doctor_id)
        slot = self._resolve_slot(doctor, slot_start, now)
        booking = Booking(
            doctor_id=doctor.id,
            patient_id=patient.id,
            chamber_id=doctor.chamber_id,
            slot_start=slot.start_utc,
            slot_end=to_utc(slot.end),
            slot_key=Booking.make_slot_key(doctor.id, slot.start_utc),
            note=note,
        )
        self.db.add(booking)
        try:
            self.db.flush()
        except IntegrityError as exc:
            # Two requests passed the availability check concurrently; the unique
            # constraint on slot_key makes exactly one of them win.
            self.db.rollback()
            raise SlotUnavailableError("slot was taken a moment ago") from exc
        self._notify(booking, "booking_confirmed")
        self.db.commit()
        self.db.refresh(booking)
        log.info(
            "booking %s created for doctor %s at %s", booking.id, doctor.id, booking.slot_start
        )
        return booking

    def cancel(
        self,
        booking_id: int,
        *,
        expected_version: int,
        reason: str | None,
        now: datetime | None = None,
    ) -> Booking:
        now = now or utcnow()
        booking = self.get_booking(booking_id)
        self._check_version(booking, expected_version)
        self.policy.assert_can_cancel(booking, now)
        booking.status = BookingStatus.CANCELLED
        booking.slot_key = None
        booking.cancelled_at = now
        booking.cancel_reason = reason
        self._notify(booking, "booking_cancelled")
        self._commit_versioned()
        self.db.refresh(booking)
        return booking

    def reschedule(
        self,
        booking_id: int,
        *,
        expected_version: int,
        new_slot_start: datetime,
        now: datetime | None = None,
    ) -> Booking:
        now = now or utcnow()
        booking = self.get_booking(booking_id)
        self._check_version(booking, expected_version)
        self.policy.assert_can_reschedule(booking, now)
        doctor = self.get_doctor(booking.doctor_id)
        slot = self._resolve_slot(doctor, new_slot_start, now)
        booking.slot_start = slot.start_utc
        booking.slot_end = to_utc(slot.end)
        booking.slot_key = Booking.make_slot_key(doctor.id, slot.start_utc)
        booking.reschedule_count += 1
        self._notify(booking, "booking_rescheduled")
        try:
            self._commit_versioned()
        except IntegrityError as exc:
            self.db.rollback()
            raise SlotUnavailableError("slot was taken a moment ago") from exc
        self.db.refresh(booking)
        return booking

    def mark(self, booking_id: int, status: BookingStatus) -> Booking:
        booking = self.get_booking(booking_id)
        if booking.status != BookingStatus.CONFIRMED:
            raise ValidationError(f"only confirmed bookings can be marked {status.value}")
        booking.status = status
        booking.slot_key = None
        self._commit_versioned()
        self.db.refresh(booking)
        return booking

    # ---- helpers -------------------------------------------------------------------
    def _check_version(self, booking: Booking, expected_version: int) -> None:
        if booking.version != expected_version:
            raise StaleVersionError(
                f"booking changed (version {booking.version}, you sent {expected_version}); "
                "reload and retry"
            )

    def _commit_versioned(self) -> None:
        try:
            self.db.commit()
        except StaleDataError as exc:
            self.db.rollback()
            raise StaleVersionError("booking was modified concurrently; reload and retry") from exc

    def _notify(self, booking: Booking, kind: str) -> None:
        doctor = booking.doctor or self.db.get(Doctor, booking.doctor_id)
        patient = booking.patient or self.db.get(Patient, booking.patient_id)
        local = to_utc(booking.slot_start).astimezone(self.tz)
        when = local.strftime("%a %d %b %Y, %I:%M %p")
        messages = {
            "booking_confirmed": (
                f"Appointment confirmed with {doctor.name} on {when}. Fee: BDT {doctor.fee_bdt}."
            ),
            "booking_cancelled": (
                f"Your appointment with {doctor.name} on {when} has been cancelled."
            ),
            "booking_rescheduled": f"Your appointment with {doctor.name} has been moved to {when}.",
        }
        self.notifier.send(
            self.db,
            channel="sms",
            recipient=patient.phone,
            kind=kind,
            body=messages[kind],
            booking_id=booking.id,
        )
