"""Public endpoints used by the patient-facing frontend."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.api.deps import DB, Config, Service
from app.api.schemas import (
    BookingCancel,
    BookingCreate,
    BookingOut,
    BookingReschedule,
    ChamberOut,
    DaySlotsOut,
    DoctorOut,
    PatientOut,
    PatientRegister,
    SlotOut,
    SpecialtyOut,
)
from app.core.errors import NotFoundError
from app.core.time import tz, utcnow
from app.db.models import Booking, Chamber, Doctor, Patient, Specialty
from app.domain.phone import normalize_bd_phone

router = APIRouter(prefix="/v1", tags=["public"])


@router.get("/specialties", response_model=list[SpecialtyOut])
def list_specialties(db: DB) -> list[Specialty]:
    return list(db.scalars(select(Specialty).order_by(Specialty.name)).all())


@router.get("/chambers", response_model=list[ChamberOut])
def list_chambers(db: DB) -> list[Chamber]:
    return list(db.scalars(select(Chamber).order_by(Chamber.area, Chamber.name)).all())


@router.get("/doctors", response_model=list[DoctorOut])
def search_doctors(
    db: DB,
    q: str | None = Query(default=None, description="name or degree contains"),
    specialty_id: int | None = None,
    area: str | None = None,
    max_fee: int | None = Query(default=None, ge=0),
) -> list[Doctor]:
    stmt = select(Doctor).where(Doctor.is_active.is_(True))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Doctor.name.ilike(like), Doctor.degrees.ilike(like)))
    if specialty_id is not None:
        stmt = stmt.where(Doctor.specialty_id == specialty_id)
    if area:
        stmt = stmt.join(Doctor.chamber).where(Chamber.area.ilike(area))
    if max_fee is not None:
        stmt = stmt.where(Doctor.fee_bdt <= max_fee)
    return list(db.scalars(stmt.order_by(Doctor.name)).unique().all())


@router.get("/doctors/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, svc: Service) -> Doctor:
    return svc.get_doctor(doctor_id)


@router.get("/doctors/{doctor_id}/slots", response_model=list[DaySlotsOut])
def doctor_slots(
    doctor_id: int,
    svc: Service,
    settings: Config,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
) -> list[DaySlotsOut]:
    zone = tz(settings.clinic_timezone)
    today = utcnow().astimezone(zone).date()
    date_from = date_from or today
    date_to = date_to or (date_from + timedelta(days=6))
    doctor = svc.get_doctor(doctor_id)
    slots = svc.slots_for(doctor, date_from, date_to)
    grouped: dict[date, list[SlotOut]] = defaultdict(list)
    for s in slots:
        grouped[s.start.date()].append(SlotOut(start=s.start, end=s.end, available=s.available))
    return [DaySlotsOut(date=d, slots=grouped[d]) for d in sorted(grouped)]


@router.post("/patients", response_model=PatientOut, status_code=201)
def register_patient(payload: PatientRegister, db: DB) -> Patient:
    """Idempotent phone registration: returns the existing patient if the phone is known."""
    phone = normalize_bd_phone(payload.phone)
    patient = db.scalar(select(Patient).where(Patient.phone == phone))
    if patient is None:
        patient = Patient(phone=phone, name=payload.name.strip())
        db.add(patient)
    else:
        patient.name = payload.name.strip()
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/patients/by-phone/{phone}", response_model=PatientOut)
def patient_by_phone(phone: str, db: DB) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.phone == normalize_bd_phone(phone)))
    if patient is None:
        raise NotFoundError("no patient registered with that phone")
    return patient


@router.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, svc: Service, db: DB) -> Booking:
    patient = db.get(Patient, payload.patient_id)
    if patient is None:
        raise NotFoundError(f"patient {payload.patient_id} not found")
    return svc.create(
        doctor_id=payload.doctor_id,
        patient=patient,
        slot_start=payload.slot_start,
        note=payload.note,
    )


@router.get("/bookings", response_model=list[BookingOut])
def list_bookings(
    db: DB,
    patient_id: int | None = None,
    phone: str | None = None,
    upcoming_only: bool = False,
) -> list[Booking]:
    stmt = select(Booking)
    if phone:
        stmt = stmt.join(Booking.patient).where(Patient.phone == normalize_bd_phone(phone))
    elif patient_id is not None:
        stmt = stmt.where(Booking.patient_id == patient_id)
    else:
        return []
    if upcoming_only:
        stmt = stmt.where(Booking.slot_start >= datetime.now(tz=tz("UTC")))
    return list(db.scalars(stmt.order_by(Booking.slot_start.desc())).unique().all())


@router.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, svc: Service) -> Booking:
    return svc.get_booking(booking_id)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, payload: BookingCancel, svc: Service) -> Booking:
    return svc.cancel(booking_id, expected_version=payload.version, reason=payload.reason)


@router.post("/bookings/{booking_id}/reschedule", response_model=BookingOut)
def reschedule_booking(booking_id: int, payload: BookingReschedule, svc: Service) -> Booking:
    return svc.reschedule(
        booking_id, expected_version=payload.version, new_slot_start=payload.slot_start
    )
