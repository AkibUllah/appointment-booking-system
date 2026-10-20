"""Timezone helpers.

All datetimes are stored in UTC and exposed to clients as timezone-aware ISO strings.
Dhaka has no daylight-saving time, but every conversion still goes through zoneinfo so
the service would keep working if the clinic timezone were changed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc


def tz(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


def ensure_aware(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC; return an aware datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def to_utc(dt: datetime) -> datetime:
    return ensure_aware(dt).astimezone(UTC)
