"""Test suite for Case Restriction privacy masking in Personal and Team Schedules."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CaseRestriction
from app.models.person import Person
from app.models.placement import CourtEvent
from app.models.user import User


@pytest.mark.asyncio
async def test_case_restriction_masks_personal_and_team_calendar_events(
    client: AsyncClient, db_session: AsyncSession, supervisor_user, caseworker_user, seed_roles_and_permissions
):
    """
    CRITICAL PRIVACY TEST:
    When a case is restricted from a user, any calendar events linked to that case
    MUST be masked to 'Unavailable / Busy' without leaking child name, case number, location, or details.
    """
    cw_user = caseworker_user["user"]
    sup_user = supervisor_user["user"]
    now = datetime.now(UTC)

    # 1. Create a Child and a Restricted Case
    child = Person(first_name="ConfidentialChild", last_name="ProtectedKin")
    db_session.add(child)
    await db_session.flush()

    restricted_case = Case(
        case_number="CAS-RESTRICTED-999",
        title="Highly Sensitive Conflict Case",
        status="Open",
        stage="INVESTIGATION",
        assigned_worker_id=sup_user.id,
    )
    db_session.add(restricted_case)
    await db_session.flush()

    # 2. Add an active CaseRestriction against the Caseworker
    restriction = CaseRestriction(
        case_id=restricted_case.id,
        user_id=cw_user.id,
        restriction_type="CONFLICT_OF_INTEREST",
        reason="Family relationship conflict of interest.",
        is_active=True,
        created_by=sup_user.id,
    )
    db_session.add(restriction)
    await db_session.flush()
    await db_session.commit()

    # 3. Supervisor creates a court hearing and an appointment linked to the restricted case
    start_dt = now + timedelta(days=3)
    end_dt = start_dt + timedelta(hours=2)

    create_res = await client.post(
        "/api/v1/calendar/events",
        json={
            "event_type": "COURT",
            "title": "Emergency Protection Hearing - Sensitive Allegations",
            "start_at": start_dt.isoformat(),
            "end_at": end_dt.isoformat(),
            "location": "Family Court Chambers 2",
            "description": "Sensitive placement and emergency custody hearing.",
            "case_id": str(restricted_case.id),
            "person_id": str(child.id),
            "assigned_user_id": str(cw_user.id),  # Worker assigned slot but restricted from case details
        },
        headers=supervisor_user["headers"],
    )
    assert create_res.status_code == 201
    evt_id = create_res.json()["id"]

    # 4. Restricted Caseworker queries My Schedule
    my_sched_res = await client.get(
        "/api/v1/calendar/my-schedule",
        params={"start_at": now.isoformat(), "end_at": (now + timedelta(days=10)).isoformat()},
        headers=caseworker_user["headers"],
    )
    assert my_sched_res.status_code == 200
    my_events = my_sched_res.json()
    masked_evt = next((e for e in my_events if e["id"] == evt_id), None)
    assert masked_evt is not None

    # Verify Strict Privacy Sanitization
    assert masked_evt["is_redacted"] is True
    assert masked_evt["title"] == "Unavailable / Busy"
    assert masked_evt["description"] is None
    assert masked_evt["location"] is None
    assert masked_evt["case_id"] is None
    assert masked_evt["case_number"] is None
    assert masked_evt["person_id"] is None
    assert masked_evt["person_name"] is None
    assert "Sensitive" not in str(masked_evt)
    assert "ProtectedKin" not in str(masked_evt)
    assert "CAS-RESTRICTED-999" not in str(masked_evt)

    # 5. Non-restricted Supervisor queries the same schedule and sees full details
    sup_sched_res = await client.get(
        "/api/v1/calendar/team-schedule",
        params={"start_at": now.isoformat(), "end_at": (now + timedelta(days=10)).isoformat()},
        headers=supervisor_user["headers"],
    )
    assert sup_sched_res.status_code == 200
    sup_events = sup_sched_res.json()
    sup_evt = next((e for e in sup_events if e["id"] == evt_id), None)
    assert sup_evt is not None
    assert sup_evt["is_redacted"] is False
    assert "Emergency Protection Hearing" in sup_evt["title"]
    assert sup_evt["case_number"] == "CAS-RESTRICTED-999"
    assert sup_evt["person_name"] == "ConfidentialChild ProtectedKin"
