"""Appointment reminders (24h and 1h before), run periodically by APScheduler."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.time import to_utc, tz, utcnow
from app.db.models import Booking, BookingStatus
from app.services.notifications import Notifier, get_notifier

log = logging.getLogger("reminders")

REMINDER_WINDOWS: dict[str, timedelta] = {
    "reminder_24h": timedelta(hours=24),
    "reminder_1h": timedelta(hours=1),
}


class ReminderService:
    def __init__(self, db: Session, settings: Settings, notifier: Notifier | None = None) -> None:
        self.db = db
        self.tz = tz(settings.clinic_timezone)
        self.notifier = notifier or get_notifier()

    def run(self, now: datetime | None = None) -> int:
        """Send every due reminder once. Returns the number of messages sent."""
        now = to_utc(now or utcnow())
        sent = 0
        for kind, lead in REMINDER_WINDOWS.items():
            column = (
                Booking.reminder_24h_sent_at
                if kind == "reminder_24h"
                else Booking.reminder_1h_sent_at
            )
            due = self.db.scalars(
                select(Booking).where(
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.slot_start > now,
                    Booking.slot_start <= now + lead,
                    column.is_(None),
                )
            ).all()
            for booking in due:
                local = to_utc(booking.slot_start).astimezone(self.tz)
                body = (
                    f"Reminder: appointment with {booking.doctor.name} at {booking.chamber.name} "
                    f"on {local.strftime('%a %d %b, %I:%M %p')}."
                )
                self.notifier.send(
                    self.db,
                    channel="sms",
                    recipient=booking.patient.phone,
                    kind=kind,
                    body=body,
                    booking_id=booking.id,
                )
                if kind == "reminder_24h":
                    booking.reminder_24h_sent_at = now
                else:
                    booking.reminder_1h_sent_at = now
                sent += 1
        self.db.commit()
        if sent:
            log.info("sent %d reminder(s)", sent)
        return sent
