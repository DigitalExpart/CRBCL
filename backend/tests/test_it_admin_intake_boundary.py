"""Regression tests enforcing the IT Admin boundary for Intake, Front Desk, Clients, and HR.

Established CRBCL Rule:
IT Admin does NOT automatically receive public-intake narratives,
Person/Client operational records, Case information, or Front Desk content
merely because they administer technical infrastructure/accounts.

Authoritative controls:
- Backend narrative endpoints MUST return 403 Forbidden to IT Admin without independent operational capability.
- IT Admin CAN perform legitimate account/system administration (e.g. /api/v1/users, /api/v1/audit/logs).
- Authorized operational roles (e.g. Front Desk, Navigator) retain their authorized access.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.front_desk import FrontDeskSubmission
from app.models.referral import Referral


@pytest.mark.anyio
async def test_it_admin_denied_front_desk_submissions_list(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to the public intake / front desk queue."""
    res = await client.get("/api/v1/front-desk/submissions", headers=it_admin_user["headers"])
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_front_desk_stats(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to front desk triage stats and counts."""
    res = await client.get("/api/v1/front-desk/stats", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_front_desk_submission_detail(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """IT Admin is denied access to view narrative details of a front desk submission."""
    sub = FrontDeskSubmission(
        submission_number="FDS-2026-TEST",
        source="phone",
        status="RECEIVED",
        urgency="Medium",
        submitter_name="Confidential Caller",
        summary="Intake narrative details",
    )
    db_session.add(sub)
    await db_session.commit()

    res = await client.get(f"/api/v1/front-desk/submissions/{sub.id}", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_manual_submission_creation(client: AsyncClient, it_admin_user: dict):
    """IT Admin cannot log front desk walk-ins or phone triage submissions."""
    payload = {
        "source": "walk_in",
        "submitter_name": "Test Submitter",
        "summary": "Walk-in inquiry",
    }
    res = await client.post("/api/v1/front-desk/submissions/manual", json=payload, headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_front_desk_routing_actions(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """IT Admin cannot route front desk submissions to departments."""
    sub = FrontDeskSubmission(
        submission_number="FDS-2026-ROUTE",
        source="phone",
        status="RECEIVED",
        urgency="Medium",
        submitter_name="Test Submitter",
        summary="Needs routing",
    )
    db_session.add(sub)
    await db_session.commit()

    route_payload = {
        "destination_department": "Prevention & Community Support",
        "urgency": "High",
        "notes": "IT admin attempted routing",
    }
    res = await client.post(
        f"/api/v1/front-desk/submissions/{sub.id}/route",
        json=route_payload,
        headers=it_admin_user["headers"],
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_referrals_list(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to list internal intake & referral records."""
    res = await client.get("/api/v1/referrals", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_referrals_stats(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to intake workload KPI statistics."""
    res = await client.get("/api/v1/referrals/stats", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_referral_approval_queue(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to the supervisory intake approval queue."""
    res = await client.get("/api/v1/referrals/approvals/queue", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_referral_detail(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """IT Admin cannot view individual referral case details or child concerns."""
    ref = Referral(
        referral_number="REF-2026-TEST",
        status="RECEIVED",
        received_date=date.today(),
        summary="Child safety concern narrative",
    )
    db_session.add(ref)
    await db_session.commit()

    res = await client.get(f"/api/v1/referrals/{ref.id}", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_client_operational_records(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to Client operational records."""
    res = await client.get("/api/v1/clients", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_case_operational_records(client: AsyncClient, it_admin_user: dict):
    """IT Admin is denied access to Case operational records."""
    res = await client.get("/api/v1/cases", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_hr_dashboard(client: AsyncClient, it_admin_user: dict):
    """IT Admin has zero protected HR permissions and cannot access HR Dashboard."""
    res = await client.get("/api/v1/org-ops/hr-dashboard", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_allowed_system_and_user_administration(client: AsyncClient, it_admin_user: dict):
    """IT Admin retains authorized capability to manage users, accounts, and system configuration."""
    users_res = await client.get("/api/v1/users", headers=it_admin_user["headers"])
    assert users_res.status_code == 200
    assert "items" in users_res.json()

    teams_res = await client.get("/api/v1/teams", headers=it_admin_user["headers"])
    assert teams_res.status_code == 200
    assert len(teams_res.json()) > 0


@pytest.mark.anyio
async def test_authorized_operational_roles_retain_intake_access(
    client: AsyncClient, navigator_user: dict, caseworker_user: dict
):
    """Operational roles retain authorized access to their respective queues."""
    nav_res = await client.get("/api/v1/referrals", headers=navigator_user["headers"])
    assert nav_res.status_code == 200

    cw_res = await client.get("/api/v1/clients", headers=caseworker_user["headers"])
    assert cw_res.status_code == 200
