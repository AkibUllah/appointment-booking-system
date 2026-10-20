"""Pydantic request/response models."""

from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models import BookingStatus, ExceptionKind


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- reference data ------------------------------------------------------------------
class SpecialtyOut(ORMModel):
    id: int
    name: str
    name_bn: str | None = None


class ChamberOut(ORMModel):
    id: int
    name: str
    area: str
    address: str
    phone: str | None = None


class DoctorOut(ORMModel):
    id: int
    name: str
    name_bn: str | None = None
    degrees: str
    specialty: SpecialtyOut
    chamber: ChamberOut
    slot_minutes: int
    fee_bdt: int
    experience_years: int
    is_active: bool


class DoctorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    name_bn: str | None = None
    degrees: str = ""
    specialty_id: int
    chamber_id: int
    slot_minutes: int = Field(default=15, ge=5, le=120)
    fee_bdt: int = Field(default=800, ge=0)
    experience_years: int = Field(default=5, ge=0, le=70)


class DoctorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    name_bn: str | None = None
    degrees: str | None = None
    slot_minutes: int | None = Field(default=None, ge=5, le=120)
    fee_bdt: int | None = Field(default=None, ge=0)
    experience_years: int | None = Field(default=None, ge=0, le=70)
    is_active: bool | None = None


# ---- availability --------------------------------------------------------------------
class TemplateBase(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: time
    end_time: time


class TemplateIn(TemplateBase):
    @model_validator(mode="after")
    def _end_after_start(self) -> TemplateIn:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class TemplateOut(TemplateBase, ORMModel):
    id: int


class ExceptionBase(BaseModel):
    on_date: date
    kind: ExceptionKind
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = Field(default=None, max_length=255)


class ExceptionIn(ExceptionBase):
    @model_validator(mode="after")
    def _window_consistent(self) -> ExceptionIn:
        if (self.start_time is None) != (self.end_time is None):
            raise ValueError("start_time and end_time must be given together")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")
        if self.kind == ExceptionKind.EXTRA and self.start_time is None:
            raise ValueError("extra sittings need a start_time and end_time")
        return self


class ExceptionOut(ExceptionBase, ORMModel):
    id: int


class SlotOut(BaseModel):
    start: datetime
    end: datetime
    available: bool


class DaySlotsOut(BaseModel):
    date: date
    slots: list[SlotOut]


# ---- patients ------------------------------------------------------------------------
class PatientRegister(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    name: str = Field(min_length=2, max_length=120)


class PatientOut(ORMModel):
    id: int
    phone: str
    name: str


# ---- bookings ------------------------------------------------------------------------
class BookingCreate(BaseModel):
    doctor_id: int
    patient_id: int
    slot_start: datetime
    note: str | None = Field(default=None, max_length=500)


class BookingCancel(BaseModel):
    version: int
    reason: str | None = Field(default=None, max_length=255)


class BookingReschedule(BaseModel):
    version: int
    slot_start: datetime


class BookingOut(ORMModel):
    id: int
    doctor: DoctorOut
    patient: PatientOut
    chamber: ChamberOut
    slot_start: datetime
    slot_end: datetime
    status: BookingStatus
    note: str | None
    reschedule_count: int
    version: int
    created_at: datetime
    cancelled_at: datetime | None
    cancel_reason: str | None


class NotificationOut(ORMModel):
    id: int
    booking_id: int | None
    channel: str
    recipient: str
    kind: str
    body: str
    sent_at: datetime


class ErrorOut(BaseModel):
    code: str
    message: str
