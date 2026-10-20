"""Admin endpoints (X-Admin-Token): doctor CRUD, schedules, exceptions, stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select

from app.api.deps import DB, Config, Service, require_admin
from app.api.schemas import (
    BookingOut,
    DoctorCreate,
    DoctorOut,
    DoctorUpdate,
    ExceptionIn,
    ExceptionOut,
    NotificationOut,
    TemplateIn,
    TemplateOut,
)
from app.core.errors import NotFoundError
from app.db.models import (
    AvailabilityException,
    AvailabilityTemplate,
    Booking,
    BookingStatus,
    Chamber,
    Doctor,
    NotificationLog,
    Specialty,
)
from app.services.reminder_service import ReminderService
from app.services.stats_service import admin_stats

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _doctor_or_404(db, doctor_id: int) -> Doctor:  # type: ignore[no-untyped-def]
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise NotFoundError(f"doctor {doctor_id} not found")
    return doctor


@router.post("/doctors", response_model=DoctorOut, status_code=201)
def create_doctor(payload: DoctorCreate, db: DB) -> Doctor:
    if db.get(Specialty, payload.specialty_id) is None:
        raise NotFoundError(f"specialty {payload.specialty_id} not found")
    if db.get(Chamber, payload.chamber_id) is None:
        raise NotFoundError(f"chamber {payload.chamber_id} not found")
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: DB) -> Doctor:
    doctor = _doctor_or_404(db, doctor_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/doctors/{doctor_id}/availability", response_model=list[TemplateOut])
def get_availability(doctor_id: int, db: DB) -> list[AvailabilityTemplate]:
    doctor = _doctor_or_404(db, doctor_id)
    return sorted(doctor.templates, key=lambda t: (t.weekday, t.start_time))


@router.put("/doctors/{doctor_id}/availability", response_model=list[TemplateOut])
def replace_availability(
    doctor_id: int, payload: list[TemplateIn], db: DB
) -> list[AvailabilityTemplate]:
    """Replace the full weekly template. Existing bookings are not touched."""
    doctor = _doctor_or_404(db, doctor_id)
    doctor.templates.clear()
    db.flush()
    for item in payload:
        doctor.templates.append(AvailabilityTemplate(**item.model_dump()))
    db.commit()
    db.refresh(doctor)
    return sorted(doctor.templates, key=lambda t: (t.weekday, t.start_time))


@router.get("/doctors/{doctor_id}/exceptions", response_model=list[ExceptionOut])
def list_exceptions(doctor_id: int, db: DB) -> list[AvailabilityException]:
    doctor = _doctor_or_404(db, doctor_id)
    return sorted(doctor.exceptions, key=lambda e: e.on_date)


@router.post("/doctors/{doctor_id}/exceptions", response_model=ExceptionOut, status_code=201)
def add_exception(doctor_id: int, payload: ExceptionIn, db: DB) -> AvailabilityException:
    doctor = _doctor_or_404(db, doctor_id)
    exc = AvailabilityException(doctor_id=doctor.id, **payload.model_dump())
    db.add(exc)
    db.commit()
    db.refresh(exc)
    return exc


@router.delete(
    "/doctors/{doctor_id}/exceptions/{exception_id}",
    status_code=204,
    response_class=Response,
    response_model=None,
)
def delete_exception(doctor_id: int, exception_id: int, db: DB) -> None:
    exc = db.get(AvailabilityException, exception_id)
    if exc is None or exc.doctor_id != doctor_id:
        raise NotFoundError("exception not found")
    db.delete(exc)
    db.commit()


@router.get("/bookings", response_model=list[BookingOut])
def all_bookings(
    db: DB,
    doctor_id: int | None = None,
    status: BookingStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Booking]:
    stmt = select(Booking)
    if doctor_id is not None:
        stmt = stmt.where(Booking.doctor_id == doctor_id)
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    return list(db.scalars(stmt.order_by(Booking.slot_start.desc()).limit(limit)).unique().all())


@router.post("/bookings/{booking_id}/complete", response_model=BookingOut)
def complete_booking(booking_id: int, svc: Service) -> Booking:
    return svc.mark(booking_id, BookingStatus.COMPLETED)


@router.post("/bookings/{booking_id}/no-show", response_model=BookingOut)
def no_show_booking(booking_id: int, svc: Service) -> Booking:
    return svc.mark(booking_id, BookingStatus.NO_SHOW)


@router.get("/stats")
def stats(db: DB, settings: Config) -> dict:
    return admin_stats(db, clinic_tz=settings.clinic_timezone)


@router.get("/notifications", response_model=list[NotificationOut])
def notifications(db: DB, limit: int = Query(default=50, ge=1, le=500)) -> list[NotificationLog]:
    return list(
        db.scalars(select(NotificationLog).order_by(NotificationLog.id.desc()).limit(limit)).all()
    )


@router.post("/reminders/run")
def run_reminders(db: DB, settings: Config) -> dict:
    return {"sent": ReminderService(db, settings).run()}
