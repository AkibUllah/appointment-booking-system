"""Notification backends. Only a console backend ships; swap in an SMS gateway here."""

from __future__ import annotations

import logging
from typing import Protocol

from sqlalchemy.orm import Session

from app.db.models import NotificationLog

log = logging.getLogger("notifications")


class Notifier(Protocol):
    def send(
        self,
        db: Session,
        *,
        channel: str,
        recipient: str,
        kind: str,
        body: str,
        booking_id: int | None,
    ) -> NotificationLog: ...


class ConsoleNotifier:
    """Logs the message and stores it in notification_log so the UI/admin can inspect it."""

    def send(
        self,
        db: Session,
        *,
        channel: str,
        recipient: str,
        kind: str,
        body: str,
        booking_id: int | None,
    ) -> NotificationLog:
        log.info("[%s -> %s] %s: %s", channel, recipient, kind, body)
        entry = NotificationLog(
            booking_id=booking_id, channel=channel, recipient=recipient, kind=kind, body=body
        )
        db.add(entry)
        db.flush()
        return entry


_default: Notifier = ConsoleNotifier()


def get_notifier() -> Notifier:
    return _default
