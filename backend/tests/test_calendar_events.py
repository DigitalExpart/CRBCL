"""Test suite for Calendar Events, Personal Schedule, Team Schedule, and Synchronization."""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.person import Person
from app.models.placement import CourtEvent
from app.models.user import User


@pytest.mark.asyncio
async def test_calendar_event_crud_and_my_schedule(
    client: AsyncClient, db_session: AsyncSession, caseworker_user, seed_roles_and_permissions
):
    """Verify creating, querying, updating, and filtering personal calendar appointments."""
    headers = caseworker_user["headers"]
    now = datetime.now(UTC)

    # 1. Create personal appointment
    start_dt = now + timedelta(days=2)
    end_dt = start_dt + timedelta(hours=1)

    payload = {
        "event_type": "APPOINTMENT",
        "title": "Family Wellness Check-in",
        "start_at": start_dt.isoformat(),
        "end_at": end_dt.isoformat(),
        "location": "CRBCL Community Centre Room 102",
        "description": "Routine quarterly family check-in discussion.",
        "status": "SCHEDULED",
    }
    create_res = await client.post("/api/v1/calendar/events", json=payload, headers=headers)
    assert create_res.status_code == 201
    evt_data = create_res.json()
    assert evt_data["title"] == "Family Wellness Check-in"
    assert evt_data["status"] == "SCHEDULED"
    event_id = evt_data["id"]

    # 2. Query My Schedule within date range
    schedule_res = await client.get(
        "/api/v1/calendar/my-schedule",
        params={"start_at": now.isoformat(), "end_at": (now + timedelta(days=5)).isoformat()},
        headers=headers,
    )
    assert schedule_res.status_code == 200
    events = schedule_res.json()
    assert any(e["id"] == event_id for e in events)

    # 3. Update appointment
    update_res = await client.patch(
        f"/api/v1/calendar/events/{event_id}",
        json={"location": "North Central Family Lodge Room 4"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["location"] == "North Central Family Lodge Room 4"

    # 4. Soft-delete appointment
    del_res = await client.delete(f"/api/v1/calendar/events/{event_id}", headers=headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_team_schedule_supervisor_access(
    client: AsyncClient, db_session: AsyncSession, supervisor_user, caseworker_user, seed_roles_and_permissions
):
    """Verify supervisor can access team schedule while caseworker without team permission is denied."""
    now = datetime.now(UTC)
    start_dt = now + timedelta(days=1)
    end_dt = start_dt + timedelta(hours=2)

    # Caseworker creates an appointment
    create_res = await client.post(
        "/api/v1/calendar/events",
        json={
            "event_type": "APPOINTMENT",
            "title": "Caseworker Home Consultation",
            "start_at": start_dt.isoformat(),
            "end_at": end_dt.isoformat(),
        },
        headers=caseworker_user["headers"],
    )
    assert create_res.status_code == 201
    evt_id = create_res.json()["id"]

    # Supervisor queries team schedule
    team_res = await client.get(
        "/api/v1/calendar/team-schedule",
        params={"start_at": now.isoformat(), "end_at": (now + timedelta(days=3)).isoformat()},
        headers=supervisor_user["headers"],
    )
    assert team_res.status_code == 200
    assert any(e["id"] == evt_id for e in team_res.json())

    # Caseworker without CALENDAR_READ_TEAM attempting to query team schedule is rejected
    cw_team_res = await client.get(
        "/api/v1/calendar/team-schedule",
        params={"start_at": now.isoformat(), "end_at": (now + timedelta(days=3)).isoformat()},
        headers=caseworker_user["headers"],
    )
    assert cw_team_res.status_code == 403


@pytest.mark.asyncio
async def test_court_event_calendar_synchronization(
    client: AsyncClient, db_session: AsyncSession, caseworker_user, seed_roles_and_permissions
):
    """Verify creating a CourtEvent automatically synchronizes representation into calendar_events."""
    headers = caseworker_user["headers"]

    # Create Case
    person = Person(first_name="Leo", last_name="Starblanket")
    db_session.add(person)
    await db_session.flush()

    case = Case(
        case_number=f"CAS-{uuid.uuid4().hex[:6].upper()}",
        title="Starblanket Family Customary Plan",
        status="Open",
        stage="INVESTIGATION",
        assigned_worker_id=caseworker_user["user"].id,
    )
    db_session.add(case)
    await db_session.flush()
    await db_session.commit()

    # Create Court Event via API
    court_payload = {
        "hearing_type": "PROTECTION_HEARING",
        "hearing_date": (date.today() + timedelta(days=14)).isoformat(),
        "hearing_time": "10:30:00",
        "court_location": "Regina Provincial Court Room 3",
        "court_docket_number": "REG-2026-9812",
        "status": "SCHEDULED",
    }
    court_res = await client.post(
        f"/api/v1/cases/{case.id}/court-events",
        json=court_payload,
        headers=headers,
    )
    assert court_res.status_code == 201
    court_data = court_res.json()

    # Query My Schedule to verify synchronized court calendar event
    sched_res = await client.get(
        "/api/v1/calendar/my-schedule",
        params={"start_at": datetime.now(UTC).isoformat(), "end_at": (datetime.now(UTC) + timedelta(days=30)).isoformat()},
        headers=headers,
    )
    assert sched_res.status_code == 200
    events = sched_res.json()
    court_cal = next((e for e in events if e.get("source_entity_id") == court_data["id"]), None)
    assert court_cal is not None
    assert court_cal["event_type"] == "COURT"
    assert "Protection Hearing" in court_cal["title"]
    assert court_cal["location"] == "Regina Provincial Court Room 3"


@pytest.mark.asyncio
async def test_case_note_next_appointment_calendar_synchronization(
    client: AsyncClient, db_session: AsyncSession, caseworker_user, seed_roles_and_permissions
):
    """Verify setting next_appointment_at on CaseNote automatically creates/updates a follow-up calendar event."""
    headers = caseworker_user["headers"]

    case = Case(
        case_number=f"CAS-{uuid.uuid4().hex[:6].upper()}",
        title="Moosehunter Family Support",
        status="Open",
        stage="ONGOING_SERVICES",
        assigned_worker_id=caseworker_user["user"].id,
    )
    db_session.add(case)
    await db_session.flush()
    await db_session.commit()

    next_appt = datetime.now(UTC) + timedelta(days=7)

    note_payload = {
        "subject": "Home visit and caregiver check",
        "content": "Discussed family routine, housing stability, and customary kinship care supports.",
        "note_type": "Progress Note",
        "contact_type": "In-Person",
        "location": "Home",
        "next_appointment_at": next_appt.isoformat(),
    }
    note_res = await client.post(
        f"/api/v1/cases/{case.id}/notes",
        json=note_payload,
        headers=headers,
    )
    assert note_res.status_code == 201
    note_data = note_res.json()

    # Query schedule to find the follow-up event
    sched_res = await client.get(
        "/api/v1/calendar/my-schedule",
        params={"start_at": datetime.now(UTC).isoformat(), "end_at": (datetime.now(UTC) + timedelta(days=14)).isoformat()},
        headers=headers,
    )
    assert sched_res.status_code == 200
    events = sched_res.json()
    followup_cal = next((e for e in events if e.get("source_entity_id") == note_data["id"]), None)
    assert followup_cal is not None
    assert followup_cal["event_type"] == "CASE_NOTE_FOLLOWUP"
    assert "Home visit" in followup_cal["title"]
