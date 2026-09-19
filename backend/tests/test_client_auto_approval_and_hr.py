"""Comprehensive verification tests for:
1. Client auto-approval for Supervisors and Directors (server-side capability based).
2. Ordinary caseworker submission leading to PENDING_APPROVAL.
3. Audit history, queue discoverability, filter accuracy, and identity preservation.
4. HR Dashboard endpoint authoritative metrics and RBAC boundary enforcement.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client, ClientApprovalHistory
from app.models.org_ops import Employee, EmployeeCertification
from app.models.person import Person


@pytest.mark.anyio
async def test_01_caseworker_creates_client_results_in_pending(
    client: AsyncClient, caseworker_user: dict
):
    """Caseworker without CLIENT_APPROVE creates new person/client -> PENDING_APPROVAL."""
    payload = {
        "person": {
            "first_name": "Tyler",
            "last_name": "Smoke",
            "date_of_birth": "2012-08-15",
            "gender": "Male",
            "primary_address": {"address_line_1": "123 Albert St", "city": "Regina"},
        },
        "risk_level": "Low",
        "submission_notes": "Caseworker family proposal.",
    }

    res = await client.post("/api/v1/clients/submit-new", json=payload, headers=caseworker_user["headers"])
    assert res.status_code == 201
    data = res.json()

    assert data["approval_status"] == "PENDING_APPROVAL"
    assert data["status"] == "Pending Intake"
    assert data["submitted_by"] == str(caseworker_user["user"].id)
    assert data["submitted_at"] is not None
    assert data["decided_by"] is None
    assert data["decided_at"] is None
    assert data["person_id_number"].startswith("11")
    assert len(data["person_id_number"]) == 10


@pytest.mark.anyio
async def test_02_caseworker_submits_existing_person_results_in_pending(
    client: AsyncClient, caseworker_user: dict, db_session: AsyncSession
):
    """Caseworker proposes existing Person as client -> PENDING_APPROVAL."""
    # Create canonical person
    p = Person(
        person_id_number="1188888881",
        first_name="Alexis",
        last_name="Cardinal",
        date_of_birth=date(2011, 4, 10),
        created_by=caseworker_user["user"].id,
        updated_by=caseworker_user["user"].id,
    )
    db_session.add(p)
    await db_session.commit()

    payload = {
        "person_id": str(p.id),
        "risk_level": "Medium",
        "submission_notes": "Existing person proposal.",
    }
    res = await client.post("/api/v1/clients/submit-existing", json=payload, headers=caseworker_user["headers"])
    assert res.status_code == 201
    data = res.json()

    assert data["approval_status"] == "PENDING_APPROVAL"
    assert data["status"] == "Pending Intake"
    assert data["person_id"] == str(p.id)
    assert data["person_id_number"] == "1188888881"


@pytest.mark.anyio
async def test_03_supervisor_direct_creation_auto_approves_immediately(
    client: AsyncClient, supervisor_user: dict, db_session: AsyncSession
):
    """Supervisor holding CLIENT_APPROVE creates new client -> APPROVED and Active immediately."""
    payload = {
        "person": {
            "first_name": "Maya",
            "last_name": "Starblanket",
            "date_of_birth": "2014-03-22",
            "gender": "Female",
        },
        "risk_level": "Low",
        "submission_notes": "Supervisor direct client intake.",
    }

    res = await client.post("/api/v1/clients/submit-new", json=payload, headers=supervisor_user["headers"])
    assert res.status_code == 201
    data = res.json()

    # Must be APPROVED and Active immediately without manual review step
    assert data["approval_status"] == "APPROVED"
    assert data["status"] == "Active"
    assert data["submitted_by"] == str(supervisor_user["user"].id)
    assert data["submitted_at"] is not None
    assert data["decided_by"] == str(supervisor_user["user"].id)
    assert data["decided_at"] is not None
    assert data["decided_by_name"] is not None
    assert data["person_id_number"].startswith("11")

    # Verify append-only history record has action APPROVED
    client_uuid = uuid.UUID(data["id"])
    hist_entries = (
        await db_session.execute(
            ClientApprovalHistory.__table__.select().where(ClientApprovalHistory.client_id == client_uuid)
        )
    ).fetchall()
    assert len(hist_entries) >= 1
    latest = hist_entries[-1]
    assert latest.action == "APPROVED"
    assert latest.to_status == "APPROVED"
    assert latest.actor_id == supervisor_user["user"].id


@pytest.mark.anyio
async def test_04_supervisor_submits_existing_person_auto_approves(
    client: AsyncClient, supervisor_user: dict, db_session: AsyncSession
):
    """Supervisor submits existing Person -> APPROVED and Active immediately."""
    p = Person(
        person_id_number="1188888882",
        first_name="Carter",
        last_name="Bear",
        date_of_birth=date(2009, 11, 5),
        created_by=supervisor_user["user"].id,
        updated_by=supervisor_user["user"].id,
    )
    db_session.add(p)
    await db_session.commit()

    payload = {
        "person_id": str(p.id),
        "risk_level": "Low",
        "submission_notes": "Supervisor direct intake for existing community member.",
    }
    res = await client.post("/api/v1/clients/submit-existing", json=payload, headers=supervisor_user["headers"])
    assert res.status_code == 201
    data = res.json()

    assert data["approval_status"] == "APPROVED"
    assert data["status"] == "Active"
    assert data["decided_by"] == str(supervisor_user["user"].id)
    assert data["decided_at"] is not None
    assert data["person_id_number"] == "1188888882"


@pytest.mark.anyio
async def test_05_director_direct_creation_auto_approves(
    client: AsyncClient, director_user: dict
):
    """Director / Service Manager holding CLIENT_APPROVE creates client -> APPROVED and Active."""
    payload = {
        "person": {
            "first_name": "Lila",
            "last_name": "Ahenakew",
            "date_of_birth": "2013-09-19",
            "gender": "Female",
        },
        "risk_level": "High",
        "submission_notes": "Director urgent intake.",
    }

    res = await client.post("/api/v1/clients/submit-new", json=payload, headers=director_user["headers"])
    assert res.status_code == 201
    data = res.json()

    assert data["approval_status"] == "APPROVED"
    assert data["status"] == "Active"
    assert data["decided_by"] == str(director_user["user"].id)
    assert data["decided_at"] is not None


@pytest.mark.anyio
async def test_06_unauthorized_staff_cannot_fake_approval_status(
    client: AsyncClient, caseworker_user: dict
):
    """Staff without CLIENT_APPROVE cannot force approval by injecting payload fields."""
    payload = {
        "person": {
            "first_name": "Sneaky",
            "last_name": "Attempt",
            "date_of_birth": "2015-01-01",
        },
        "risk_level": "Low",
        "approval_status": "APPROVED",
        "status": "Active",
    }
    res = await client.post("/api/v1/clients/submit-new", json=payload, headers=caseworker_user["headers"])
    assert res.status_code == 201
    data = res.json()
    # Server authority overrides any client payload attempts
    assert data["approval_status"] == "PENDING_APPROVAL"
    assert data["status"] == "Pending Intake"
    assert data["decided_by"] is None


@pytest.mark.anyio
async def test_07_pending_proposals_appear_in_supervisor_and_director_queue(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, director_user: dict
):
    """Caseworker proposal appears in /approvals/pending for both Supervisor and Director."""
    payload = {
        "person": {
            "first_name": "Evan",
            "last_name": "Queued",
            "date_of_birth": "2016-02-14",
        },
        "risk_level": "Medium",
        "submission_notes": "Awaiting review.",
    }
    create_res = await client.post("/api/v1/clients/submit-new", json=payload, headers=caseworker_user["headers"])
    assert create_res.status_code == 201
    client_id = create_res.json()["id"]

    # Supervisor queue check
    sup_q = await client.get("/api/v1/clients/approvals/pending", headers=supervisor_user["headers"])
    assert sup_q.status_code == 200
    sup_items = sup_q.json()["items"]
    assert any(item["client_id"] == client_id for item in sup_items)

    # Director queue check
    dir_q = await client.get("/api/v1/clients/approvals/pending", headers=director_user["headers"])
    assert dir_q.status_code == 200
    dir_items = dir_q.json()["items"]
    assert any(item["client_id"] == client_id for item in dir_items)


@pytest.mark.anyio
async def test_08_client_directory_filters_respect_approval_status(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Clients directory accurately filters by approval_status query param."""
    # Create 1 pending (caseworker) and 1 approved (supervisor)
    c1 = await client.post(
        "/api/v1/clients/submit-new",
        json={"person": {"first_name": "Pending", "last_name": "FilterTest", "date_of_birth": "2010-01-01"}},
        headers=caseworker_user["headers"],
    )
    c2 = await client.post(
        "/api/v1/clients/submit-new",
        json={"person": {"first_name": "Approved", "last_name": "FilterTest", "date_of_birth": "2010-02-02"}},
        headers=supervisor_user["headers"],
    )

    c1_id = c1.json()["id"]
    c2_id = c2.json()["id"]

    # Filter PENDING_APPROVAL
    p_res = await client.get("/api/v1/clients?approval_status=PENDING_APPROVAL", headers=caseworker_user["headers"])
    assert p_res.status_code == 200
    p_ids = [item["id"] for item in p_res.json()["items"]]
    assert c1_id in p_ids
    assert c2_id not in p_ids

    # Filter APPROVED
    a_res = await client.get("/api/v1/clients?approval_status=APPROVED", headers=caseworker_user["headers"])
    assert a_res.status_code == 200
    a_ids = [item["id"] for item in a_res.json()["items"]]
    assert c2_id in a_ids
    assert c1_id not in a_ids


@pytest.mark.anyio
async def test_09_prevent_duplicate_client_for_same_person(
    client: AsyncClient, supervisor_user: dict
):
    """Submitting an already approved client returns 409 ALREADY_CLIENT without duplicating Person."""
    first = await client.post(
        "/api/v1/clients/submit-new",
        json={"person": {"first_name": "Duplicate", "last_name": "Guard", "date_of_birth": "2012-12-12"}},
        headers=supervisor_user["headers"],
    )
    assert first.status_code == 201
    person_id = first.json()["person_id"]

    # Re-submitting existing person who is already approved
    second = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": person_id, "risk_level": "Low"},
        headers=supervisor_user["headers"],
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "ALREADY_CLIENT"


@pytest.mark.anyio
async def test_10_hr_dashboard_authoritative_metrics(
    client: AsyncClient, hr_user: dict, db_session: AsyncSession
):
    """HR Dashboard returns authoritative counts and correctly handles unmodeled metrics."""
    # Seed 2 employees: 1 Active, 1 On Leave
    e1 = Employee(
        employee_number="EMP-101",
        first_name="Tara",
        last_name="HRTest",
        email="tara.hr@crbcl.ca",
        position="Social Worker",
        department="Child Safety",
        employment_status="ACTIVE",
        hire_date=date.today() - timedelta(days=20),
    )
    e2 = Employee(
        employee_number="EMP-102",
        first_name="Brian",
        last_name="HRTest",
        email="brian.hr@crbcl.ca",
        position="Youth Mentor",
        department="Prevention",
        employment_status="ON_LEAVE",
        hire_date=date.today() - timedelta(days=120),
    )
    db_session.add_all([e1, e2])
    await db_session.flush()

    # Seed an expiring certification for e1
    cert = EmployeeCertification(
        employee_id=e1.id,
        cert_type="First Aid & CPR",
        identifier="CPR-999",
        issued_date=date.today() - timedelta(days=330),
        expiry_date=date.today() + timedelta(days=15),  # within 30 days
        status="ACTIVE",
    )
    db_session.add(cert)
    await db_session.commit()

    res = await client.get("/api/v1/org-ops/hr-dashboard", headers=hr_user["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["total_employees"] >= 2
    assert data["active_staff_count"] >= 1
    assert data["on_leave_count"] >= 1
    assert data["recent_hires_count"] >= 1
    assert "Child Safety" in data["department_distribution"]
    assert data["expiring_soon_count"] >= 1

    # Verify unmodeled metrics are explicitly flagged is_available=False
    assert data["fte_metrics"]["is_available"] is False
    assert data["turnover_rate"]["is_available"] is False
    assert data["retention_targets"]["is_available"] is False
    assert data["leave_balances"]["is_available"] is False
    assert data["formal_onboarding_pipeline"]["is_available"] is False


@pytest.mark.anyio
async def test_11_hr_dashboard_rbac_enforcement(
    client: AsyncClient, director_user: dict, caseworker_user: dict, it_admin_user: dict
):
    """Director has access to HR dashboard; Caseworker and IT Admin are rejected (403)."""
    # Director has HR_DASHBOARD_READ
    dir_res = await client.get("/api/v1/org-ops/hr-dashboard", headers=director_user["headers"])
    assert dir_res.status_code == 200

    # Caseworker is forbidden
    cw_res = await client.get("/api/v1/org-ops/hr-dashboard", headers=caseworker_user["headers"])
    assert cw_res.status_code == 403

    # IT Admin is forbidden (system administration != personnel records)
    it_res = await client.get("/api/v1/org-ops/hr-dashboard", headers=it_admin_user["headers"])
    assert it_res.status_code == 403
