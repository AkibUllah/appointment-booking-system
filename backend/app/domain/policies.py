"""Cancellation / reschedule policies as pure functions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.errors import PolicyViolationError
from app.core.time import to_utc
from app.db.models import Booking, BookingStatus


@dataclass(frozen=True)
class BookingPolicy:
    cancel_min_hours_before: int = 2
    reschedule_min_hours_before: int = 2
    max_reschedules: int = 2

    def assert_can_cancel(self, booking: Booking, now: datetime) -> None:
        if booking.status != BookingStatus.CONFIRMED:
            raise PolicyViolationError(
                f"cannot cancel a booking in status '{booking.status.value}'"
            )
        deadline = to_utc(booking.slot_start) - timedelta(hours=self.cancel_min_hours_before)
        if to_utc(now) > deadline:
            raise PolicyViolationError(
                f"cancellation closes {self.cancel_min_hours_before}h before the appointment"
            )

    def assert_can_reschedule(self, booking: Booking, now: datetime) -> None:
        if booking.status != BookingStatus.CONFIRMED:
            raise PolicyViolationError(
                f"cannot reschedule a booking in status '{booking.status.value}'"
            )
        if booking.reschedule_count >= self.max_reschedules:
            raise PolicyViolationError(
                f"a booking may be rescheduled at most {self.max_reschedules} times"
            )
        deadline = to_utc(booking.slot_start) - timedelta(hours=self.reschedule_min_hours_before)
        if to_utc(now) > deadline:
            raise PolicyViolationError(
                f"rescheduling closes {self.reschedule_min_hours_before}h before the appointment"
            )
