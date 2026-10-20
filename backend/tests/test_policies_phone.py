from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.errors import PolicyViolationError, ValidationError
from app.db.models import Booking, BookingStatus
from app.domain.phone import normalize_bd_phone
from app.domain.policies import BookingPolicy

SLOT = datetime(2026, 3, 1, 11, 0, tzinfo=timezone.utc)


def booking(**kw):  # type: ignore[no-untyped-def]
    b = Booking(
        doctor_id=1,
        patient_id=1,
        chamber_id=1,
        slot_start=SLOT,
        slot_end=SLOT + timedelta(minutes=15),
    )
    b.status = kw.get("status", BookingStatus.CONFIRMED)
    b.reschedule_count = kw.get("reschedule_count", 0)
    return b


def test_cancel_allowed_before_deadline() -> None:
    BookingPolicy(cancel_min_hours_before=2).assert_can_cancel(booking(), SLOT - timedelta(hours=3))


def test_cancel_rejected_inside_deadline() -> None:
    with pytest.raises(PolicyViolationError, match="closes 2h"):
        BookingPolicy(cancel_min_hours_before=2).assert_can_cancel(
            booking(), SLOT - timedelta(minutes=90)
        )


def test_cancel_rejected_for_non_confirmed() -> None:
    with pytest.raises(PolicyViolationError):
        BookingPolicy().assert_can_cancel(
            booking(status=BookingStatus.CANCELLED), SLOT - timedelta(days=1)
        )


def test_reschedule_limit_enforced() -> None:
    policy = BookingPolicy(max_reschedules=2)
    policy.assert_can_reschedule(booking(reschedule_count=1), SLOT - timedelta(days=1))
    with pytest.raises(PolicyViolationError, match="at most 2"):
        policy.assert_can_reschedule(booking(reschedule_count=2), SLOT - timedelta(days=1))


def test_reschedule_deadline_enforced() -> None:
    with pytest.raises(PolicyViolationError, match="rescheduling closes"):
        BookingPolicy(reschedule_min_hours_before=4).assert_can_reschedule(
            booking(), SLOT - timedelta(hours=3)
        )


@pytest.mark.parametrize(
    "raw",
    ["01712345678", "+8801712345678", "8801712345678", "017-1234-5678", " 01712 345678 "],
)
def test_phone_normalisation_variants(raw: str) -> None:
    assert normalize_bd_phone(raw) == "+8801712345678"


@pytest.mark.parametrize(
    "raw", ["0171234567", "01212345678", "+4401712345678", "abc", "02-9123456"]
)
def test_phone_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValidationError):
        normalize_bd_phone(raw)
