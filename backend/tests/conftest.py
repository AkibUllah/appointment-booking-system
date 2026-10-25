"""Shared fixtures: in-memory SQLite, overridden dependencies, seeded doctor."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import datetime, time, timezone

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["ADMIN_TOKEN"] = "test-admin-token"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db import session as db_session  # noqa: E402
from app.db.models import (  # noqa: E402
    AvailabilityTemplate,
    Base,
    Chamber,
    Doctor,
    Patient,
    Specialty,
)
from app.main import app  # noqa: E402

ADMIN = {"X-Admin-Token": "test-admin-token"}
# A fixed "now": Sunday 2026-03-01 09:00 Dhaka (03:00 UTC). Doctor sits Sun/Tue/Thu 17-21.
NOW = datetime(2026, 3, 1, 3, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _fresh_schema() -> Iterator[None]:
    Base.metadata.drop_all(bind=db_session.engine)
    Base.metadata.create_all(bind=db_session.engine)
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    factory = sessionmaker(bind=db_session.engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def settings():  # type: ignore[no-untyped-def]
    return get_settings()


@pytest.fixture
def doctor(db: Session) -> Doctor:
    spec = Specialty(name="Cardiology", name_bn="হৃদরোগ")
    chamber = Chamber(name="Sunflower Dhanmondi", area="Dhanmondi", address="Road 4, Dhanmondi")
    db.add_all([spec, chamber])
    db.flush()
    doc = Doctor(
        name="Dr. Farhana Rahman",
        degrees="MBBS, MD",
        specialty_id=spec.id,
        chamber_id=chamber.id,
        slot_minutes=15,
        fee_bdt=1200,
    )
    for weekday in (6, 1, 3):  # Sunday, Tuesday, Thursday
        doc.templates.append(
            AvailabilityTemplate(weekday=weekday, start_time=time(17, 0), end_time=time(21, 0))
        )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@pytest.fixture
def patient(db: Session) -> Patient:
    p = Patient(phone="+8801712345678", name="Rahim Uddin")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
