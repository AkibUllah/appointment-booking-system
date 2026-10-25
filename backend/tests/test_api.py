"""HTTP-level tests through FastAPI TestClient."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from tests.conftest import ADMIN


def next_weekday(weekday: int, after: date) -> date:
    d = after + timedelta(days=1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def setup_doctor(client: TestClient) -> int:
    from sqlalchemy import select

    from app.db import session as db_session
    from app.db.models import Chamber, Specialty

    with db_session.SessionLocal() as db:
        db.add_all(
            [
                Specialty(name="ENT", name_bn="নাক-কান-গলা"),
                Chamber(name="Riverbank Shyamoli", area="Shyamoli", address="Mirpur Road"),
            ]
        )
        db.commit()
        spec_id = db.scalar(select(Specialty.id))
        chamber_id = db.scalar(select(Chamber.id))
    r = client.post(
        "/v1/admin/doctors",
        json={
            "name": "Dr. Rezaul Karim",
            "degrees": "MBBS, DLO",
            "specialty_id": spec_id,
            "chamber_id": chamber_id,
            "slot_minutes": 10,
            "fee_bdt": 700,
        },
        headers=ADMIN,
    )
    assert r.status_code == 201, r.text
    doctor_id = r.json()["id"]
    r = client.put(
        f"/v1/admin/doctors/{doctor_id}/availability",
        json=[{"weekday": wd, "start_time": "17:00:00", "end_time": "21:00:00"} for wd in range(7)],
        headers=ADMIN,
    )
    assert r.status_code == 200 and len(r.json()) == 7
    return doctor_id


def register(client: TestClient, phone: str = "01812345678") -> int:
    r = client.post("/v1/patients", json={"phone": phone, "name": "Karim Mia"})
    assert r.status_code == 201
    assert r.json()["phone"] == "+8801812345678"
    return r.json()["id"]


def first_free_slot(client: TestClient, doctor_id: int) -> str:
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    r = client.get(
        f"/v1/doctors/{doctor_id}/slots",
        params={"from": tomorrow.isoformat(), "to": tomorrow.isoformat()},
    )
    assert r.status_code == 200, r.text
    days = r.json()
    assert days and days[0]["slots"]
    slot = next(s for s in days[0]["slots"] if s["available"])
    assert slot["start"].endswith("+06:00")
    return slot["start"]


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_admin_requires_token(client: TestClient) -> None:
    assert client.get("/v1/admin/stats").status_code == 401
    assert client.get("/v1/admin/stats", headers={"X-Admin-Token": "wrong"}).status_code == 401


def test_doctor_search_filters(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    assert client.get("/v1/doctors").json()[0]["id"] == doctor_id
    assert client.get("/v1/doctors", params={"q": "rezaul"}).json()
    assert client.get("/v1/doctors", params={"q": "nobody"}).json() == []
    assert client.get("/v1/doctors", params={"area": "shyamoli"}).json()
    assert client.get("/v1/doctors", params={"max_fee": 500}).json() == []
    assert client.get("/v1/doctors/999").status_code == 404


def test_full_booking_flow(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    patient_id = register(client)
    slot = first_free_slot(client, doctor_id)

    r = client.post(
        "/v1/bookings", json={"doctor_id": doctor_id, "patient_id": patient_id, "slot_start": slot}
    )
    assert r.status_code == 201, r.text
    booking = r.json()
    assert booking["status"] == "confirmed" and booking["version"] == 1

    # the same slot is now unavailable and a second booking is rejected with 409
    r = client.post(
        "/v1/bookings", json={"doctor_id": doctor_id, "patient_id": patient_id, "slot_start": slot}
    )
    assert r.status_code == 409 and r.json()["code"] == "slot_unavailable"

    r = client.get("/v1/bookings", params={"phone": "01812345678"})
    assert [b["id"] for b in r.json()] == [booking["id"]]

    # stale version -> 409
    r = client.post(f"/v1/bookings/{booking['id']}/cancel", json={"version": 5})
    assert r.status_code == 409 and r.json()["code"] == "stale_version"

    r = client.post(f"/v1/bookings/{booking['id']}/cancel", json={"version": 1, "reason": "travel"})
    assert r.status_code == 200 and r.json()["status"] == "cancelled" and r.json()["version"] == 2

    notes = client.get("/v1/admin/notifications", headers=ADMIN).json()
    assert {n["kind"] for n in notes} == {"booking_confirmed", "booking_cancelled"}


def test_reschedule_via_api(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    patient_id = register(client)
    slot = first_free_slot(client, doctor_id)
    booking = client.post(
        "/v1/bookings", json={"doctor_id": doctor_id, "patient_id": patient_id, "slot_start": slot}
    ).json()
    new_start = (datetime.fromisoformat(slot) + timedelta(minutes=10)).isoformat()
    r = client.post(
        f"/v1/bookings/{booking['id']}/reschedule", json={"version": 1, "slot_start": new_start}
    )
    assert r.status_code == 200, r.text
    assert r.json()["reschedule_count"] == 1
    returned = r.json()["slot_start"].replace("Z", "+00:00")
    assert datetime.fromisoformat(returned) == datetime.fromisoformat(new_start)


def test_leave_exception_hides_slots(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    r = client.post(
        f"/v1/admin/doctors/{doctor_id}/exceptions",
        json={"on_date": day.isoformat(), "kind": "leave", "reason": "conference"},
        headers=ADMIN,
    )
    assert r.status_code == 201
    r = client.get(
        f"/v1/doctors/{doctor_id}/slots", params={"from": day.isoformat(), "to": day.isoformat()}
    )
    assert r.json() == []
    exc_id = client.get(f"/v1/admin/doctors/{doctor_id}/exceptions", headers=ADMIN).json()[0]["id"]
    assert (
        client.delete(
            f"/v1/admin/doctors/{doctor_id}/exceptions/{exc_id}", headers=ADMIN
        ).status_code
        == 204
    )
    r = client.get(
        f"/v1/doctors/{doctor_id}/slots", params={"from": day.isoformat(), "to": day.isoformat()}
    )
    assert len(r.json()[0]["slots"]) == 24


def test_exception_validation(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    r = client.post(
        f"/v1/admin/doctors/{doctor_id}/exceptions",
        json={"on_date": "2026-05-01", "kind": "extra"},
        headers=ADMIN,
    )
    assert r.status_code == 422


def test_slot_range_too_far_ahead_rejected(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    far = (datetime.now(timezone.utc) + timedelta(days=90)).date().isoformat()
    r = client.get(f"/v1/doctors/{doctor_id}/slots", params={"from": far, "to": far})
    assert r.status_code == 422 and r.json()["code"] == "validation_error"


def test_patient_registration_is_idempotent_and_validated(client: TestClient) -> None:
    a = register(client)
    b = register(client)
    assert a == b
    r = client.post("/v1/patients", json={"phone": "12345", "name": "X Y"})
    assert r.status_code == 422
    r = client.get("/v1/patients/by-phone/01812345678")
    assert r.status_code == 200 and r.json()["id"] == a


def test_admin_stats_and_manual_reminder_run(client: TestClient) -> None:
    doctor_id = setup_doctor(client)
    patient_id = register(client)
    slot = first_free_slot(client, doctor_id)
    client.post(
        "/v1/bookings", json={"doctor_id": doctor_id, "patient_id": patient_id, "slot_start": slot}
    )
    stats = client.get("/v1/admin/stats", headers=ADMIN).json()
    assert stats["total_bookings"] == 1
    assert stats["by_status"]["confirmed"] == 1
    assert stats["per_doctor"][0]["bookings"] == 1
    r = client.post("/v1/admin/reminders/run", headers=ADMIN)
    assert r.status_code == 200 and r.json()["sent"] in (0, 1)
