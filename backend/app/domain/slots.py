"""Pure slot-generation logic.

Given a doctor's weekly templates, date-specific exceptions and existing bookings, produce
the list of bookable slots for a date range in the clinic timezone. No database access
here so it is straightforward to unit test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.time import to_utc
from app.db.models import AvailabilityException, AvailabilityTemplate, ExceptionKind


@dataclass(frozen=True)
class Slot:
    start: datetime  # aware, clinic timezone
    end: datetime
    available: bool

    @property
    def start_utc(self) -> datetime:
        return to_utc(self.start)


@dataclass(frozen=True)
class Window:
    start: time
    end: time


def _windows_for_day(
    day: date,
    templates: list[AvailabilityTemplate],
    exceptions: list[AvailabilityException],
) -> list[Window]:
    day_exceptions = [e for e in exceptions if e.on_date == day]
    # A whole-day leave removes every window, including extras.
    if any(e.kind == ExceptionKind.LEAVE and e.start_time is None for e in day_exceptions):
        return []
    windows = [Window(t.start_time, t.end_time) for t in templates if t.weekday == day.weekday()]
    windows += [
        Window(e.start_time, e.end_time)
        for e in day_exceptions
        if e.kind == ExceptionKind.EXTRA and e.start_time and e.end_time
    ]
    return sorted(windows, key=lambda w: w.start)


def _blocked_ranges(day: date, exceptions: list[AvailabilityException]) -> list[Window]:
    return [
        Window(e.start_time, e.end_time)
        for e in exceptions
        if e.on_date == day and e.kind == ExceptionKind.LEAVE and e.start_time and e.end_time
    ]


def _overlaps(slot_start: time, slot_end: time, blocked: Window) -> bool:
    return slot_start < blocked.end and blocked.start < slot_end


def generate_slots(
    *,
    templates: list[AvailabilityTemplate],
    exceptions: list[AvailabilityException],
    booked_starts_utc: set[datetime],
    slot_minutes: int,
    date_from: date,
    date_to: date,
    tzinfo: ZoneInfo,
    now: datetime,
    min_lead: timedelta = timedelta(minutes=30),
) -> list[Slot]:
    """Return every slot in [date_from, date_to] inclusive, flagged available or not.

    Slots that start before ``now + min_lead`` are omitted entirely rather than flagged,
    so clients never see the past.
    """
    if slot_minutes <= 0:
        raise ValueError("slot_minutes must be positive")
    if date_to < date_from:
        raise ValueError("date_to must not be before date_from")

    step = timedelta(minutes=slot_minutes)
    cutoff = to_utc(now) + min_lead
    booked = {to_utc(b) for b in booked_starts_utc}
    slots: list[Slot] = []

    day = date_from
    while day <= date_to:
        blocked = _blocked_ranges(day, exceptions)
        for window in _windows_for_day(day, templates, exceptions):
            start = datetime.combine(day, window.start, tzinfo=tzinfo)
            window_end = datetime.combine(day, window.end, tzinfo=tzinfo)
            while start + step <= window_end:
                end = start + step
                if any(
                    _overlaps(
                        start.timetz().replace(tzinfo=None), end.timetz().replace(tzinfo=None), b
                    )
                    for b in blocked
                ):
                    start = end
                    continue
                if to_utc(start) >= cutoff:
                    slots.append(Slot(start=start, end=end, available=to_utc(start) not in booked))
                start = end
        day += timedelta(days=1)
    slots.sort(key=lambda s: s.start)
    return slots


def find_slot(slots: list[Slot], start_utc: datetime) -> Slot | None:
    target = to_utc(start_utc)
    for s in slots:
        if s.start_utc == target:
            return s
    return None
