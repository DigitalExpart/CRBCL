"""Integration tests verifying full administrative access to all staff dashboards.

CRBCL Rule:
Admin Dashboard and Administrator accounts (System Administrator, admin@crbcl.ca,
it_admin, and admin roles) have full administrative and operational access to all
staff dashboards across the platform, including Front Desk, Office Coordinator,
Navigator/Intake, Referrals, Clients, Cases, Fleet, Board, and HR.

Authoritative controls:
- Backend endpoints return 200 OK (or 201 Created for creation) to Administrator.
- Administrator can view, route, and manage operational workflows across all staff domains.
- Non-admin staff roles retain their authorized operational access.
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
async def test_it_admin_has_front_desk_submissions_list(client: AsyncClient, it_admin_user: dict):
    """Administrator has operational access to the public intake / front desk queue."""
    res = await client.get("/api/v1/front-desk/submissions", headers=it_admin_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "items" in data


@pytest.mark.anyio
async def test_it_admin_has_front_desk_stats(client: AsyncClient, it_admin_user: dict):
    """Administrator has access to front desk triage stats and counts."""
    res = await client.get("/api/v1/front-desk/stats", headers=it_admin_user["headers"])
    assert res.status_code == 200
    assert "total_count" in res.json()


@pytest.mark.anyio
async def test_it_admin_has_front_desk_submission_detail(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """Administrator has access to view narrative details of a front desk submission."""
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
    assert res.status_code == 200
    assert res.json()["id"] == str(sub.id)


@pytest.mark.anyio
async def test_it_admin_can_create_manual_submission(client: AsyncClient, it_admin_user: dict):
    """Administrator can log front desk walk-ins or phone triage submissions."""
    payload = {
        "source": "walk_in",
        "submitter_name": "Test Submitter",
        "summary": "Walk-in inquiry",
    }
    res = await client.post("/api/v1/front-desk/submissions/manual", json=payload, headers=it_admin_user["headers"])
    assert res.status_code == 201
    assert res.json()["status"] == "RECEIVED"


@pytest.mark.anyio
async def test_it_admin_can_route_front_desk_submission(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """Administrator can route front desk submissions to departments."""
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
        "notes": "Admin routing to department",
    }
    res = await client.post(
        f"/api/v1/front-desk/submissions/{sub.id}/route",
        json=route_payload,
        headers=it_admin_user["headers"],
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ROUTED"


@pytest.mark.anyio
async def test_it_admin_has_referrals_list(client: AsyncClient, it_admin_user: dict):
    """Administrator has operational access to list internal intake & referral records."""
    res = await client.get("/api/v1/referrals", headers=it_admin_user["headers"])
    assert res.status_code == 200
    assert "items" in res.json()


@pytest.mark.anyio
async def test_it_admin_has_referrals_stats(client: AsyncClient, it_admin_user: dict):
    """Administrator has access to intake workload KPI statistics."""
    res = await client.get("/api/v1/referrals/stats", headers=it_admin_user["headers"])
    assert res.status_code == 200


@pytest.mark.anyio
async def test_it_admin_has_referral_approval_queue(client: AsyncClient, it_admin_user: dict):
    """Administrator has access to the supervisory intake approval queue."""
    res = await client.get("/api/v1/referrals/approvals/queue", headers=it_admin_user["headers"])
    assert res.status_code == 200


@pytest.mark.anyio
async def test_it_admin_has_referral_detail(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """Administrator can view individual referral case details."""
    ref = Referral(
        referral_number="REF-2026-TEST",
        status="RECEIVED",
        received_date=date.today(),
        summary="Child safety concern narrative",
    )
    db_session.add(ref)
    await db_session.commit()

    res = await client.get(f"/api/v1/referrals/{ref.id}", headers=it_admin_user["headers"])
    assert res.status_code == 200
    assert res.json()["id"] == str(ref.id)


@pytest.mark.anyio
async def test_it_admin_has_client_operational_records(client: AsyncClient, it_admin_user: dict):
    """Administrator has access to Client operational records."""
    res = await client.get("/api/v1/clients", headers=it_admin_user["headers"])
    assert res.status_code == 200


@pytest.mark.anyio
async def test_it_admin_has_case_operational_records(client: AsyncClient, it_admin_user: dict):
    """Administrator has access to Case operational records."""
    res = await client.get("/api/v1/cases", headers=it_admin_user["headers"])
    assert res.status_code == 200


@pytest.mark.anyio
async def test_it_admin_has_hr_dashboard(client: AsyncClient, it_admin_user: dict):
    """Administrator has access to HR Dashboard."""
    res = await client.get("/api/v1/org-ops/hr-dashboard", headers=it_admin_user["headers"])
    assert res.status_code == 200


@pytest.mark.anyio
async def test_it_admin_allowed_system_and_user_administration(client: AsyncClient, it_admin_user: dict):
    """Administrator retains authorized capability to manage users, accounts, and system configuration."""
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
