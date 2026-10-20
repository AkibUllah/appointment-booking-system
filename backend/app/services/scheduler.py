"""APScheduler wiring for the reminder job."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import Settings
from app.db.session import SessionLocal
from app.services.reminder_service import ReminderService

log = logging.getLogger("scheduler")


def _reminder_job(settings: Settings) -> None:
    db = SessionLocal()
    try:
        ReminderService(db, settings).run()
    except Exception:  # noqa: BLE001 - keep the scheduler alive
        log.exception("reminder job failed")
        db.rollback()
    finally:
        db.close()


def build_scheduler(settings: Settings) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=settings.clinic_timezone)
    scheduler.add_job(
        _reminder_job,
        "interval",
        seconds=settings.reminder_interval_seconds,
        args=[settings],
        id="send_reminders",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
