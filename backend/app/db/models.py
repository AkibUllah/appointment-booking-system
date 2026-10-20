"""ORM models."""

from __future__ import annotations

import enum
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.time import UTC, to_utc


class UTCDateTime(TypeDecorator[datetime]):
    """Stores aware datetimes as naive UTC and always returns aware UTC values.

    SQLite drops tzinfo, so normalising on both sides keeps behaviour identical
    between SQLite (tests/dev) and Postgres (compose).
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:  # type: ignore[override]
        if value is None:
            return None
        return to_utc(value).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:  # type: ignore[override]
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class Specialty(Base):
    __tablename__ = "specialties"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    name_bn: Mapped[str | None] = mapped_column(String(80))

    doctors: Mapped[list[Doctor]] = relationship(back_populates="specialty")


class Chamber(Base):
    __tablename__ = "chambers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    area: Mapped[str] = mapped_column(String(60), index=True)
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    name_bn: Mapped[str | None] = mapped_column(String(120))
    degrees: Mapped[str] = mapped_column(String(255), default="")
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id"))
    chamber_id: Mapped[int] = mapped_column(ForeignKey("chambers.id"))
    slot_minutes: Mapped[int] = mapped_column(Integer, default=15)
    fee_bdt: Mapped[int] = mapped_column(Integer, default=800)
    experience_years: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    specialty: Mapped[Specialty] = relationship(back_populates="doctors", lazy="joined")
    chamber: Mapped[Chamber] = relationship(lazy="joined")
    templates: Mapped[list[AvailabilityTemplate]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )
    exceptions: Mapped[list[AvailabilityException]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )


class AvailabilityTemplate(Base):
    """Weekly recurring window: doctor sits at the chamber on `weekday` from start to end."""

    __tablename__ = "availability_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Monday ... 6=Sunday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    doctor: Mapped[Doctor] = relationship(back_populates="templates")


class ExceptionKind(str, enum.Enum):
    LEAVE = "leave"  # doctor unavailable (whole day or a window)
    EXTRA = "extra"  # additional sitting outside the weekly template


class AvailabilityException(Base):
    __tablename__ = "availability_exceptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    on_date: Mapped[date] = mapped_column(Date)
    kind: Mapped[ExceptionKind] = mapped_column(Enum(ExceptionKind, native_enum=False, length=10))
    start_time: Mapped[time | None] = mapped_column(Time)  # None + LEAVE = whole day off
    end_time: Mapped[time | None] = mapped_column(Time)
    reason: Mapped[str | None] = mapped_column(String(255))

    doctor: Mapped[Doctor] = relationship(back_populates="exceptions")


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(
        String(14), unique=True, index=True
    )  # normalised +8801XXXXXXXXX
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=lambda: datetime.now(UTC))


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("slot_key", name="uq_booking_slot_key"),
        Index("ix_bookings_doctor_start", "doctor_id", "slot_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    chamber_id: Mapped[int] = mapped_column(ForeignKey("chambers.id"))
    slot_start: Mapped[datetime] = mapped_column(UTCDateTime)
    slot_end: Mapped[datetime] = mapped_column(UTCDateTime)
    # "<doctor_id>:<slot_start iso>" while active, NULL once cancelled. The unique
    # constraint on this column is the last line of defence against double booking.
    slot_key: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, native_enum=False, length=12), default=BookingStatus.CONFIRMED
    )
    note: Mapped[str | None] = mapped_column(Text)
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    cancel_reason: Mapped[str | None] = mapped_column(String(255))
    reminder_24h_sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    reminder_1h_sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    __mapper_args__ = {"version_id_col": version}

    doctor: Mapped[Doctor] = relationship(lazy="joined")
    patient: Mapped[Patient] = relationship(lazy="joined")
    chamber: Mapped[Chamber] = relationship(lazy="joined")

    @staticmethod
    def make_slot_key(doctor_id: int, slot_start: datetime) -> str:
        return f"{doctor_id}:{to_utc(slot_start).strftime('%Y%m%dT%H%M')}"


class NotificationLog(Base):
    """Every message the console notifier would have sent (SMS/email) is recorded here."""

    __tablename__ = "notification_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), index=True)
    channel: Mapped[str] = mapped_column(String(10))  # sms | email
    recipient: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(30))  # booking_confirmed, reminder_24h, ...
    body: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(UTCDateTime, default=lambda: datetime.now(UTC))
