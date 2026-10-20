"""Admin statistics."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import to_utc, tz
from app.db.models import Booking, BookingStatus, Doctor


def admin_stats(db: Session, *, clinic_tz: str, today: date | None = None) -> dict:
    zone = tz(clinic_tz)
    today = today or datetime.now(zone).date()
    day_start = to_utc(datetime.combine(today, datetime.min.time(), tzinfo=zone))
    day_end = day_start + timedelta(days=1)
    week_end = day_start + timedelta(days=7)

    by_status = {
        status.value: count
        for status, count in db.execute(
            select(Booking.status, func.count()).group_by(Booking.status)
        ).all()
    }
    for s in BookingStatus:
        by_status.setdefault(s.value, 0)

    today_count = (
        db.scalar(
            select(func.count()).where(
                Booking.slot_start >= day_start,
                Booking.slot_start < day_end,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        or 0
    )
    upcoming_week = (
        db.scalar(
            select(func.count()).where(
                Booking.slot_start >= day_start,
                Booking.slot_start < week_end,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        or 0
    )

    per_doctor_rows = db.execute(
        select(Doctor.id, Doctor.name, func.count(Booking.id))
        .join(Booking, Booking.doctor_id == Doctor.id, isouter=True)
        .where(Doctor.is_active.is_(True))
        .group_by(Doctor.id, Doctor.name)
        .order_by(func.count(Booking.id).desc())
    ).all()

    total = sum(by_status.values())
    cancelled = by_status.get(BookingStatus.CANCELLED.value, 0)
    return {
        "date": today.isoformat(),
        "total_bookings": total,
        "by_status": by_status,
        "today_confirmed": today_count,
        "next_7_days_confirmed": upcoming_week,
        "cancellation_rate": round(cancelled / total, 3) if total else 0.0,
        "per_doctor": [
            {"doctor_id": did, "doctor_name": name, "bookings": count}
            for did, name, count in per_doctor_rows
        ],
    }
