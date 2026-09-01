"""Test suite for Staffing Facilitator, attendee rosters, review workflows, and triage buckets."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.staffing import StaffingAttendee, StaffingCase, StaffingSession
from app.models.team import Team
from app.models.user import User


@pytest.mark.asyncio
async def test_staffing_session_lifecycle_and_attendance(
    client: AsyncClient, db_session: AsyncSession, supervisor_user, caseworker_user, seed_roles_and_permissions
):
    """Verify staffing session creation, attendee tracking, case review state machine, and completion command."""
    sup_headers = supervisor_user["headers"]
    cw_user = caseworker_user["user"]
    sup_user = supervisor_user["user"]

    # 1. Create a Team and Case
    team = Team(name="Family Preservation North Team", code="FPN-01")
    db_session.add(team)
    await db_session.flush()

    case = Case(
        case_number=f"CAS-{uuid.uuid4().hex[:6].upper()}",
        title="Papequash Kinship Case",
        status="Open",
        stage="ONGOING_SERVICES",
        assigned_team_id=team.id,
        assigned_worker_id=cw_user.id,
        risk_level="Medium",
    )
    db_session.add(case)
    await db_session.flush()
    await db_session.commit()

    # 2. Create Staffing Session
    session_dt = datetime.now(UTC) + timedelta(days=2)
    session_payload = {
        "title": "North Unit Bi-Weekly Staffing",
        "session_date": session_dt.isoformat(),
        "team_id": str(team.id),
        "facilitator_id": str(sup_user.id),
        "cadence": "BIWEEKLY",
        "status": "SCHEDULED",
        "location": "Boardroom B / Teams",
        "attendee_ids": [str(cw_user.id)],
        "case_ids": [str(case.id)],
    }
    create_res = await client.post("/api/v1/staffing/sessions", json=session_payload, headers=sup_headers)
    assert create_res.status_code == 201
    sess_data = create_res.json()
    sess_id = sess_data["id"]
    assert sess_data["title"] == "North Unit Bi-Weekly Staffing"
    assert len(sess_data["attendees"]) == 1
    assert len(sess_data["cases"]) == 1

    # 3. Update Attendee presence
    att_res = await client.post(
        f"/api/v1/staffing/sessions/{sess_id}/attendees",
        json={
            "user_id": str(cw_user.id),
            "attendance_status": "ATTENDED",
            "notes": "Presented case progression and safety plan updates.",
        },
        headers=sup_headers,
    )
    assert att_res.status_code == 201
    assert att_res.json()["attendance_status"] == "ATTENDED"

    # 4. Update Case Review Outcome
    review_res = await client.patch(
        f"/api/v1/staffing/sessions/{sess_id}/cases/{case.id}",
        json={
            "review_status": "REVIEWED",
            "discussion_summary": "Kinship placement stable. Supervised visits progressing well. Ready for unsupervised transition plan.",
            "follow_up_required": True,
            "follow_up_date": (date.today() + timedelta(days=14)).isoformat(),
            "assigned_worker_id": str(cw_user.id),
        },
        headers=sup_headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["review_status"] == "REVIEWED"
    assert review_res.json()["follow_up_required"] is True

    # 5. Complete Session
    complete_res = await client.post(
        f"/api/v1/staffing/sessions/{sess_id}/complete",
        json={"minutes": "Session adjourned at 11:45 AM. All action items assigned."},
        headers=sup_headers,
    )
    assert complete_res.status_code == 200
    comp_data = complete_res.json()
    assert comp_data["status"] == "COMPLETED"
    assert "adjourned at 11:45" in comp_data["minutes"]


@pytest.mark.asyncio
async def test_staffing_automated_triage_buckets(
    client: AsyncClient, db_session: AsyncSession, supervisor_user, caseworker_user, seed_roles_and_permissions
):
    """Verify server-side automated triage buckets (Not staffed 90+ days, Open 12+ months, High Risk, Missing recent notes)."""
    headers = supervisor_user["headers"]
    cw_user = caseworker_user["user"]
    past_100_days = date.today() - timedelta(days=100)
    past_400_days = date.today() - timedelta(days=400)

    # Case 1: Open >90 days, never staffed
    case_90 = Case(
        case_number=f"CAS-90D-{uuid.uuid4().hex[:4].upper()}",
        title="Never Staffed Case",
        status="Open",
        stage="INVESTIGATION",
        intake_date=past_100_days,
        assigned_worker_id=cw_user.id,
    )
    db_session.add(case_90)

    # Case 2: Open 12+ months
    case_12m = Case(
        case_number=f"CAS-12M-{uuid.uuid4().hex[:4].upper()}",
        title="Long Term Open Case",
        status="Open",
        stage="ONGOING_SERVICES",
        intake_date=past_400_days,
        assigned_worker_id=cw_user.id,
    )
    db_session.add(case_12m)

    # Case 3: High Risk
    case_risk = Case(
        case_number=f"CAS-HR-{uuid.uuid4().hex[:4].upper()}",
        title="Immediate Safety Concern Case",
        status="Open",
        stage="INVESTIGATION",
        risk_level="High",
        assigned_worker_id=cw_user.id,
    )
    db_session.add(case_risk)

    await db_session.flush()
    await db_session.commit()

    # Query Buckets
    buckets_res = await client.get("/api/v1/staffing/case-buckets", headers=headers)
    assert buckets_res.status_code == 200
    data = buckets_res.json()

    # Verify bucket memberships
    assert any(c["case_id"] == str(case_90.id) for c in data["not_staffed_90_days"])
    assert any(c["case_id"] == str(case_12m.id) for c in data["open_12_months"])
    assert any(c["case_id"] == str(case_risk.id) for c in data["high_risk"])
