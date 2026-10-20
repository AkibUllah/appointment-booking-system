"""Slot generation in Asia/Dhaka (UTC+6, no DST)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.db.models import AvailabilityException, AvailabilityTemplate, ExceptionKind
from app.domain.slots import find_slot, generate_slots

DHAKA = ZoneInfo("Asia/Dhaka")
SUNDAY = date(2026, 3, 1)  # 2026-03-01 is a Sunday
EARLY = datetime(2026, 2, 20, 0, 0, tzinfo=timezone.utc)


def tpl(weekday: int, start: str, end: str) -> AvailabilityTemplate:
    return AvailabilityTemplate(
        weekday=weekday, start_time=time.fromisoformat(start), end_time=time.fromisoformat(end)
    )


def exc(on: date, kind: ExceptionKind, start: str | None = None, end: str | None = None):
    return AvailabilityException(
        on_date=on,
        kind=kind,
        start_time=time.fromisoformat(start) if start else None,
        end_time=time.fromisoformat(end) if end else None,
    )


def gen(**overrides):  # type: ignore[no-untyped-def]
    params = dict(
        templates=[tpl(6, "17:00", "21:00")],
        exceptions=[],
        booked_starts_utc=set(),
        slot_minutes=15,
        date_from=SUNDAY,
        date_to=SUNDAY,
        tzinfo=DHAKA,
        now=EARLY,
    )
    params.update(overrides)
    return generate_slots(**params)


def test_generates_contiguous_slots_within_window() -> None:
    slots = gen()
    assert len(slots) == 16  # 4 hours / 15 min
    assert slots[0].start == datetime(2026, 3, 1, 17, 0, tzinfo=DHAKA)
    assert slots[-1].end == datetime(2026, 3, 1, 21, 0, tzinfo=DHAKA)
    for a, b in zip(slots, slots[1:], strict=False):
        assert a.end == b.start


def test_slots_are_dhaka_local_and_utc_offset_is_plus_six() -> None:
    slots = gen()
    first = slots[0]
    assert first.start.utcoffset() == timedelta(hours=6)
    assert first.start_utc == datetime(2026, 3, 1, 11, 0, tzinfo=timezone.utc)


def test_no_slots_on_days_without_template() -> None:
    monday = SUNDAY + timedelta(days=1)
    assert gen(date_from=monday, date_to=monday) == []


def test_partial_slot_at_window_end_is_dropped() -> None:
    slots = gen(templates=[tpl(6, "17:00", "17:50")], slot_minutes=20)
    assert [s.start.strftime("%H:%M") for s in slots] == ["17:00", "17:20"]


def test_whole_day_leave_removes_all_slots() -> None:
    assert gen(exceptions=[exc(SUNDAY, ExceptionKind.LEAVE)]) == []


def test_partial_leave_blocks_overlapping_slots_only() -> None:
    slots = gen(exceptions=[exc(SUNDAY, ExceptionKind.LEAVE, "18:00", "19:00")])
    starts = {s.start.strftime("%H:%M") for s in slots}
    assert len(slots) == 12
    assert "18:00" not in starts and "18:45" not in starts
    assert "17:45" in starts and "19:00" in starts


def test_extra_sitting_adds_window_on_otherwise_free_day() -> None:
    monday = SUNDAY + timedelta(days=1)
    slots = gen(
        date_from=monday,
        date_to=monday,
        exceptions=[exc(monday, ExceptionKind.EXTRA, "10:00", "11:00")],
    )
    assert [s.start.strftime("%H:%M") for s in slots] == ["10:00", "10:15", "10:30", "10:45"]


def test_whole_day_leave_also_cancels_extra_sitting() -> None:
    slots = gen(
        exceptions=[
            exc(SUNDAY, ExceptionKind.LEAVE),
            exc(SUNDAY, ExceptionKind.EXTRA, "09:00", "10:00"),
        ]
    )
    assert slots == []


def test_booked_slot_is_flagged_unavailable() -> None:
    booked = {datetime(2026, 3, 1, 11, 15, tzinfo=timezone.utc)}  # 17:15 Dhaka
    slots = gen(booked_starts_utc=booked)
    by_time = {s.start.strftime("%H:%M"): s.available for s in slots}
    assert by_time["17:15"] is False
    assert by_time["17:00"] is True
    assert sum(1 for s in slots if not s.available) == 1


def test_slots_before_now_plus_lead_are_omitted() -> None:
    # now = 18:10 Dhaka, 30 minutes lead -> first slot 18:45
    now = datetime(2026, 3, 1, 18, 10, tzinfo=DHAKA)
    slots = gen(now=now, min_lead=timedelta(minutes=30))
    assert slots[0].start.strftime("%H:%M") == "18:45"


def test_multi_day_range_sorted_and_only_template_days() -> None:
    templates = [tpl(6, "17:00", "18:00"), tpl(1, "09:00", "10:00")]
    slots = gen(templates=templates, date_from=SUNDAY, date_to=SUNDAY + timedelta(days=6))
    days = sorted({s.start.date() for s in slots})
    assert days == [SUNDAY, SUNDAY + timedelta(days=2)]
    assert slots == sorted(slots, key=lambda s: s.start)


def test_find_slot_matches_by_utc_instant() -> None:
    slots = gen()
    found = find_slot(slots, datetime(2026, 3, 1, 11, 30, tzinfo=timezone.utc))
    assert found is not None and found.start.strftime("%H:%M") == "17:30"
    assert find_slot(slots, datetime(2026, 3, 1, 11, 37, tzinfo=timezone.utc)) is None


def test_invalid_arguments_raise() -> None:
    with pytest.raises(ValueError):
        gen(slot_minutes=0)
    with pytest.raises(ValueError):
        gen(date_to=SUNDAY - timedelta(days=1))
