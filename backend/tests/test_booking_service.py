"""Booking service: double booking, optimistic locking, policies, reminders."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import SlotUnavailableError, StaleVersionError
from app.db.models import Booking, BookingStatus, NotificationLog
from app.services.booking_service import BookingService
from app.services.reminder_service import ReminderService
from tests.conftest import NOW

SLOT_1700 = datetime(2026, 3, 1, 11, 0, tzinfo=timezone.utc)  # Sun 17:00 Dhaka
SLOT_1715 = SLOT_1700 + timedelta(minutes=15)


def svc(db: Session, settings) -> BookingService:  # type: ignore[no-untyped-def]
    return BookingService(db, settings)


def test_create_booking_and_confirmation_notification(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    b = svc(db, settings).create(
        doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW
    )
    assert b.status == BookingStatus.CONFIRMED
    assert b.slot_start == SLOT_1700 and b.slot_end == SLOT_1715
    assert b.version == 1
    notes = db.scalars(select(NotificationLog)).all()
    assert len(notes) == 1 and notes[0].kind == "booking_confirmed" and "05:00 PM" in notes[0].body


def test_double_booking_same_slot_rejected(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    with pytest.raises(SlotUnavailableError, match="already booked"):
        s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    assert (
        db.scalar(select(Booking).where(Booking.status == BookingStatus.CONFIRMED).limit(1))
        is not None
    )
    assert len(db.scalars(select(Booking)).all()) == 1


def test_unique_slot_key_catches_race(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    """Simulate two requests passing the availability check: the DB constraint decides."""
    s = svc(db, settings)
    s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    racer = Booking(
        doctor_id=doctor.id,
        patient_id=patient.id,
        chamber_id=doctor.chamber_id,
        slot_start=SLOT_1700,
        slot_end=SLOT_1715,
        slot_key=Booking.make_slot_key(doctor.id, SLOT_1700),
    )
    db.add(racer)
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_booking_off_grid_time_rejected(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SlotUnavailableError, match="not a bookable slot"):
        svc(db, settings).create(
            doctor_id=doctor.id,
            patient=patient,
            slot_start=SLOT_1700 + timedelta(minutes=7),
            now=NOW,
        )


def test_booking_on_leave_day_rejected(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    from datetime import date

    from app.db.models import AvailabilityException, ExceptionKind

    db.add(
        AvailabilityException(
            doctor_id=doctor.id, on_date=date(2026, 3, 1), kind=ExceptionKind.LEAVE
        )
    )
    db.commit()
    db.refresh(doctor)
    with pytest.raises(SlotUnavailableError):
        svc(db, settings).create(
            doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW
        )


def test_cancel_frees_slot_and_bumps_version(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    b = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    cancelled = s.cancel(b.id, expected_version=1, reason="feeling better", now=NOW)
    assert cancelled.status == BookingStatus.CANCELLED
    assert cancelled.version == 2
    assert cancelled.slot_key is None
    # slot is bookable again
    again = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    assert again.id != b.id


def test_cancel_with_stale_version_rejected(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    b = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    with pytest.raises(StaleVersionError):
        s.cancel(b.id, expected_version=99, reason=None, now=NOW)
    db.refresh(b)
    assert b.status == BookingStatus.CONFIRMED


def test_cancel_inside_policy_window_rejected(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    from app.core.errors import PolicyViolationError

    s = svc(db, settings)
    b = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    with pytest.raises(PolicyViolationError):
        s.cancel(b.id, expected_version=1, reason=None, now=SLOT_1700 - timedelta(minutes=30))


def test_reschedule_moves_slot_and_counts(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    b = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    moved = s.reschedule(b.id, expected_version=1, new_slot_start=SLOT_1715, now=NOW)
    assert moved.slot_start == SLOT_1715
    assert moved.reschedule_count == 1 and moved.version == 2
    # the old slot is free, the new one is taken
    slots = s.slots_for(doctor, SLOT_1700.date(), SLOT_1700.date(), now=NOW)
    avail = {sl.start_utc: sl.available for sl in slots}
    assert avail[SLOT_1700] is True and avail[SLOT_1715] is False


def test_reschedule_into_taken_slot_rejected(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    a = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1715, now=NOW)
    with pytest.raises(SlotUnavailableError):
        s.reschedule(a.id, expected_version=1, new_slot_start=SLOT_1715, now=NOW)


def test_reschedule_limit(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    from app.core.errors import PolicyViolationError

    s = svc(db, settings)
    b = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    b = s.reschedule(b.id, expected_version=1, new_slot_start=SLOT_1715, now=NOW)
    b = s.reschedule(b.id, expected_version=2, new_slot_start=SLOT_1700, now=NOW)
    with pytest.raises(PolicyViolationError, match="at most"):
        s.reschedule(b.id, expected_version=3, new_slot_start=SLOT_1715, now=NOW)


def test_reminders_sent_once_per_window(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    reminders = ReminderService(db, settings)
    assert reminders.run(now=SLOT_1700 - timedelta(hours=30)) == 0
    assert reminders.run(now=SLOT_1700 - timedelta(hours=20)) == 1  # 24h reminder
    assert reminders.run(now=SLOT_1700 - timedelta(hours=20)) == 0  # not repeated
    assert reminders.run(now=SLOT_1700 - timedelta(minutes=50)) == 1  # 1h reminder
    kinds = [n.kind for n in db.scalars(select(NotificationLog)).all()]
    assert kinds.count("reminder_24h") == 1 and kinds.count("reminder_1h") == 1


def test_cancelled_bookings_get_no_reminder(db, settings, doctor, patient) -> None:  # type: ignore[no-untyped-def]
    s = svc(db, settings)
    b = s.create(doctor_id=doctor.id, patient=patient, slot_start=SLOT_1700, now=NOW)
    s.cancel(b.id, expected_version=1, reason=None, now=NOW)
    assert ReminderService(db, settings).run(now=SLOT_1700 - timedelta(hours=1)) == 0
