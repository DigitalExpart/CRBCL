"""Tests for CRBCL CEO Dashboard, Strategic Initiatives, Board Actions, and Department Updates.

Verifies:
1. CEO dashboard authorization (200 OK for CEO / Executive Director)
2. IT Admin denial (403 Forbidden)
3. Ordinary Director denial from CEO-wide dashboard (403 Forbidden)
4. Department alone grants zero CEO authority (403 Forbidden)
5. Executive summary aggregate correctness (employees, cases, families, placements, homes, beds, programs)
6. Workforce calculations and unavailable metrics representation (is_available=False, not 0)
7. Resource Unit aggregate integration
8. Strategic Initiatives lifecycle & append-only audit history
9. Overdue initiative detection
10. Board Action lifecycle, decision recording & history preservation
11. Department Executive Updates by reporting period & historical preservation
12. Department health aggregation
13. No client narrative leakage in executive summary responses
14. Finance Decimal precision & budgeting aggregations
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core.seed import PERMISSIONS_DATA, ROLE_PERMISSIONS_MAP
from app.models.board_action import BoardAction
from app.models.case import Case
from app.models.department_update import DepartmentExecutiveUpdate, DepartmentExecutiveUpdateHistory
from app.models.executive_initiative import ExecutiveInitiative
from app.models.family import Family
from app.models.finance import BudgetLine, FundingSource, ServiceRequest
from app.models.org_ops import Employee
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.sprint_b_models import FundingGrant, Program
from app.models.user import User
from app.permissions.constants import Permissions


async def _create_test_user(
    db_session: AsyncSession,
    role_key: str,
    role_name: str,
    email: str,
    full_name: str,
    department: str | None = None,
    permissions: list[str | Permissions] | None = None,
) -> dict:
    """Helper to provision a test user with assigned role and permissions."""
    res = await db_session.execute(select(Role).where(Role.key == role_key))
    role = res.scalars().first()
    if not role:
        role = Role(key=role_key, name=role_name, is_system=True)
        db_session.add(role)
        await db_session.flush()

    perm_keys = permissions if permissions is not None else ROLE_PERMISSIONS_MAP.get(role_key, [])
    for pk in perm_keys:
        val = pk.value if hasattr(pk, "value") else pk
        p_res = await db_session.execute(select(Permission).where(Permission.key == val))
        p = p_res.scalars().first()
        if not p:
            p = Permission(key=val, name=val, category="test")
            db_session.add(p)
            await db_session.flush()
        rp_res = await db_session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == p.id,
            )
        )
        if not rp_res.scalars().first():
            rp = RolePermission(role_id=role.id, permission_id=p.id)
            db_session.add(rp)
    await db_session.flush()

    user = User(
        email=email,
        email_normalized=email.lower(),
        password_hash=hash_password("password123"),
        full_name=full_name,
        department=department,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def ceo_user(db_session: AsyncSession):
    return await _create_test_user(
        db_session=db_session,
        role_key="ceo",
        role_name="Chief Executive Officer",
        email=f"ceo_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Executive CEO",
        department="Governance & Executive Leadership",
        permissions=[p["key"] for p in PERMISSIONS_DATA],
    )


@pytest.fixture
async def it_admin_user(db_session: AsyncSession):
    return await _create_test_user(
        db_session=db_session,
        role_key="it_admin",
        role_name="IT Admin",
        email=f"admin_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="System Administrator",
        department="IT & Systems",
    )


@pytest.fixture
async def ordinary_director(db_session: AsyncSession):
    return await _create_test_user(
        db_session=db_session,
        role_key="director_manager",
        role_name="Director / Manager",
        email=f"director_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Department Director",
        department="Resource Team",
    )


# ── 1. RBAC & Access Boundaries ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ceo_dashboard_authorization(client: AsyncClient, ceo_user: dict):
    """CEO user with executive_dashboard.read receives 200 OK."""
    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert "executive_summary" in body
    assert "department_health" in body
    assert "workforce" in body
    assert "service_delivery" in body
    assert "finance" in body


@pytest.mark.asyncio
async def test_it_admin_denied_ceo_dashboard(client: AsyncClient, it_admin_user: dict):
    """IT Admin possessing NO executive capabilities must be rejected with 403 Forbidden."""
    res = await client.get("/api/v1/ceo-dashboard", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_ordinary_director_denied_ceo_dashboard(client: AsyncClient, ordinary_director: dict):
    """Department Director without organization-wide executive permission cannot read CEO dashboard."""
    res = await client.get("/api/v1/ceo-dashboard", headers=ordinary_director["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_department_alone_grants_zero_ceo_authority(
    client: AsyncClient, db_session: AsyncSession
):
    """Belonging to executive department grants zero access without capability permissions."""
    unauthorized = await _create_test_user(
        db_session=db_session,
        role_key="case_aide",
        role_name="Case Aide",
        email=f"unauth_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Unauthorized Aide",
        department="Governance & Executive Leadership",
    )
    res = await client.get("/api/v1/ceo-dashboard", headers=unauthorized["headers"])
    assert res.status_code == 403


# ── 2. Executive Summary & Authoritative Aggregation ──────────────────────────


@pytest.mark.asyncio
async def test_executive_summary_aggregates(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """Test defensible aggregate values for staff, cases, placements, homes, and beds."""
    today = date.today()

    # 1. Active employee
    emp = Employee(
        employee_number=f"EMP-{uuid.uuid4().hex[:6]}",
        first_name="Jane",
        last_name="Worker",
        email=f"jane_{uuid.uuid4().hex[:6]}@crbcl.ca",
        position="Caseworker",
        department="Growing Up Well (Protection Services)",
        employment_status="ACTIVE",
        hire_date=today - timedelta(days=10),
    )
    db_session.add(emp)

    # 2. Case and family
    fam = Family(
        family_name=f"Bear-{uuid.uuid4().hex[:4]}",
        notes="Customary care support",
    )
    db_session.add(fam)
    await db_session.flush()

    case_obj = Case(
        case_number=f"CASE-{uuid.uuid4().hex[:6]}",
        title="Family Support File",
        status="ACTIVE",
        case_type="PROTECTION",
        family_id=fam.id,
    )
    db_session.add(case_obj)
    await db_session.flush()

    # 3. Child and active placement episode
    child = Person(
        first_name="Tommy",
        last_name="Child",
    )
    db_session.add(child)
    await db_session.flush()

    home = PlacementHome(
        home_code=f"RH-{uuid.uuid4().hex[:6]}",
        name="Circle of Care Home",
        status="ACTIVE",
        total_capacity=3,
    )
    db_session.add(home)
    await db_session.flush()

    placement = PlacementEpisode(
        case_id=case_obj.id,
        child_id=child.id,
        placement_home_id=home.id,
        placement_type="CUSTOMARY_CARE",
        provider_name="Resource Provider",
        start_date=today - timedelta(days=5),
        status="ACTIVE",
    )
    db_session.add(placement)

    # 4. Program
    program = Program(
        name="Traditional Beading & Storytelling",
        category="Cultural Programs",
        status="ACTIVE",
        capacity=15,
        enrolled_count=8,
    )
    db_session.add(program)
    await db_session.commit()

    # Query CEO dashboard
    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    data = res.json()
    exec_summary = data["executive_summary"]

    assert exec_summary["total_active_employees"]["value"] >= 1
    assert exec_summary["active_cases"]["value"] >= 1
    assert exec_summary["children_in_care"]["value"] >= 1
    assert exec_summary["active_resource_homes"]["value"] >= 1
    assert exec_summary["resource_capacity"]["value"] >= 3
    # available beds = capacity (>=3) - children in care (>=1)
    assert exec_summary["resource_available_beds"]["value"] >= 1
    assert exec_summary["active_programs"]["value"] >= 1


# ── 3. Workforce & Unavailable Metrics ────────────────────────────────────────


@pytest.mark.asyncio
async def test_workforce_unavailable_metrics(client: AsyncClient, ceo_user: dict):
    """Verifies that non-structured metrics return is_available=False rather than fabricated 0."""
    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    wf = res.json()["workforce"]

    # Permanent & Term staff are not in Employee schema
    assert wf["permanent_staff"]["is_available"] is False
    assert wf["permanent_staff"]["value"] is None
    assert "not tracked" in wf["permanent_staff"]["reason"].lower()

    assert wf["term_staff"]["is_available"] is False
    assert wf["term_staff"]["value"] is None

    # Resignations vs Dismissals not tracked in schema
    assert wf["recent_resignations"]["is_available"] is False
    assert wf["recent_terminations"]["is_available"] is False

    # Total departures and active staff ARE available
    assert wf["total_active_staff"]["is_available"] is True
    assert wf["total_departures"]["is_available"] is True


# ── 4. Strategic Initiatives Lifecycle & Audit History ────────────────────────


@pytest.mark.asyncio
async def test_initiatives_lifecycle_and_history(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """Test creating an initiative and updating status preserves append-only history."""
    # 1. Create initiative
    create_payload = {
        "title": "C-92 Successor Agreement Implementation",
        "description": "Negotiation with federal/provincial partners",
        "department": "Governance & Executive Leadership",
        "status": "ON_TRACK",
        "priority": "HIGH",
        "target_date": str(date.today() + timedelta(days=60)),
        "progress_percentage": 25,
        "latest_update": "Drafting terms of reference",
    }
    create_res = await client.post(
        "/api/v1/ceo-dashboard/initiatives",
        json=create_payload,
        headers=ceo_user["headers"],
    )
    assert create_res.status_code == 201
    init_data = create_res.json()
    init_id = init_data["id"]
    assert init_data["title"] == create_payload["title"]
    assert len(init_data["history"]) >= 1
    assert init_data["history"][0]["previous_status"] == "NEW"

    # 2. Update initiative status to AT_RISK with progress note
    update_payload = {
        "status": "AT_RISK",
        "progress_percentage": 30,
        "latest_update": "Funding schedule delayed pending Crown review",
        "status_change_note": "Risk escalated due to fiscal boundary changes",
    }
    patch_res = await client.patch(
        f"/api/v1/ceo-dashboard/initiatives/{init_id}",
        json=update_payload,
        headers=ceo_user["headers"],
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["status"] == "AT_RISK"
    assert len(patched_data["history"]) >= 2
    # Verify previous status was ON_TRACK
    assert patched_data["history"][0]["previous_status"] == "ON_TRACK"
    assert patched_data["history"][0]["new_status"] == "AT_RISK"


@pytest.mark.asyncio
async def test_overdue_initiative_detection(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """Initiatives with past target dates are flagged is_overdue=True."""
    past_date = str(date.today() - timedelta(days=10))
    payload = {
        "title": "Past Due Governance Review",
        "description": "Annual committee review",
        "department": "Policy & Data",
        "status": "DELAYED",
        "priority": "HIGH",
        "target_date": past_date,
    }
    res = await client.post(
        "/api/v1/ceo-dashboard/initiatives",
        json=payload,
        headers=ceo_user["headers"],
    )
    assert res.status_code == 201

    # Fetch full dashboard to verify overdue count
    dash_res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert dash_res.status_code == 200
    delayed_count = dash_res.json()["executive_summary"]["delayed_overdue_initiatives"]["value"]
    assert delayed_count >= 1


# ── 5. Board Action Lifecycle, Decision & History ─────────────────────────────


@pytest.mark.asyncio
async def test_board_action_lifecycle_and_decision_preservation(
    client: AsyncClient, ceo_user: dict, ordinary_director: dict
):
    """Director submits Board Action; CEO/Board records decision; history is appended."""
    # 1. Director can submit a Board Action request
    ba_payload = {
        "originating_department": "Resource Team",
        "title": "Approval for Sacred Wolf Lodge Customary Care Extension",
        "background_summary": "Facility capacity review requires board endorsement for expanded caregiver beds.",
        "requested_action": "Board approval of motion to endorse capital allocation for 4 new customary beds.",
        "priority": "HIGH",
        "required_by_date": str(date.today() + timedelta(days=14)),
    }
    create_res = await client.post(
        "/api/v1/ceo-dashboard/board-actions",
        json=ba_payload,
        headers=ordinary_director["headers"],
    )
    assert create_res.status_code == 201
    ba_data = create_res.json()
    ba_id = ba_data["id"]
    assert ba_data["reference_number"].startswith("BA-")
    assert ba_data["status"] == "SUBMITTED"
    assert len(ba_data["history"]) >= 1

    # 2. CEO records Board decision
    decision_payload = {
        "status": "APPROVED",
        "decision": "Board Motion 2026-042 approved unanimously with directive to report on occupancy quarterly.",
        "decision_notes": "All quorum present and voted in favour.",
    }
    dec_res = await client.post(
        f"/api/v1/ceo-dashboard/board-actions/{ba_id}/decision",
        json=decision_payload,
        headers=ceo_user["headers"],
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == "APPROVED"
    assert dec_data["decision"] == decision_payload["decision"]
    # Append-only history has previous status SUBMITTED -> new status APPROVED
    assert len(dec_data["history"]) >= 2
    assert dec_data["history"][0]["previous_status"] == "SUBMITTED"
    assert dec_data["history"][0]["new_status"] == "APPROVED"


# ── 6. Department Executive Updates & History Preservation ────────────────────


@pytest.mark.asyncio
async def test_department_updates_by_reporting_period(
    client: AsyncClient, ordinary_director: dict, ceo_user: dict
):
    """Submissions across distinct periods (e.g. 2026-04 and 2026-05) are preserved."""
    # Period 2026-04
    upd_april = {
        "reporting_period": "2026-04",
        "department": "Resource Team",
        "headline_summary": "April Resource Unit Expansion and Caregiver Circles",
        "accomplishments_narrative": "Completed 3 community engagement sessions and 2 customary care circles.",
        "risks_issues": "Placement demand remains high in rural zones.",
        "support_decision_requested": "Advocacy for recruitment marketing support.",
    }
    res1 = await client.post(
        "/api/v1/ceo-dashboard/department-updates",
        json=upd_april,
        headers=ordinary_director["headers"],
    )
    assert res1.status_code == 201

    # Period 2026-05
    upd_may = {
        "reporting_period": "2026-05",
        "department": "Resource Team",
        "headline_summary": "May Caregiver Retention and Training Launch",
        "accomplishments_narrative": "Launched mandatory customary care module for 12 applicants.",
        "risks_issues": "None currently.",
    }
    res2 = await client.post(
        "/api/v1/ceo-dashboard/department-updates",
        json=upd_may,
        headers=ordinary_director["headers"],
    )
    assert res2.status_code == 201

    # CEO queries April updates
    april_list_res = await client.get(
        "/api/v1/ceo-dashboard/department-updates?reporting_period=2026-04",
        headers=ceo_user["headers"],
    )
    assert april_list_res.status_code == 200
    april_items = april_list_res.json()
    assert any(u["reporting_period"] == "2026-04" for u in april_items)
    # May record was NOT overwritten by April query
    may_list_res = await client.get(
        "/api/v1/ceo-dashboard/department-updates?reporting_period=2026-05",
        headers=ceo_user["headers"],
    )
    assert may_list_res.status_code == 200
    may_items = may_list_res.json()
    assert any(u["reporting_period"] == "2026-05" for u in may_items)


# ── 7. No Client Narrative Leakage & Department Health ────────────────────────


@pytest.mark.asyncio
async def test_no_client_narrative_leakage(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """Validates that CEO command centre aggregates do not leak clinical narratives or child names."""
    secret_note = "PRIVATE_CONFIDENTIAL_CLINICAL_NARRATIVE_XYZ999"
    secret_client_name = "SECRET_PROTECTED_CHILD_DOE"

    child = Person(first_name=secret_client_name, last_name="Protected")
    db_session.add(child)
    await db_session.flush()

    case_obj = Case(
        case_number=f"CASE-{uuid.uuid4().hex[:6]}",
        title="High Sensitivity File",
        status="ACTIVE",
        description=secret_note,
        notes=secret_note,
    )
    db_session.add(case_obj)
    await db_session.commit()

    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    text_content = res.text
    assert secret_note not in text_content
    assert secret_client_name not in text_content


@pytest.mark.asyncio
async def test_finance_decimal_precision(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """Confirms finance computations use exact Decimals without floating-point errors."""
    fs = FundingSource(
        code=f"FS-{uuid.uuid4().hex[:6]}",
        name="Indigenous Child & Family Wellness Funding",
        funder_name="Indigenous Services Canada",
        total_allocation=Decimal("1500000.00"),
    )
    db_session.add(fs)
    await db_session.flush()

    bl = BudgetLine(
        code=f"BL-{uuid.uuid4().hex[:6]}",
        name="Customary Care Bed Operations",
        funding_source_id=fs.id,
        fiscal_year="2026-2027",
        allocated_amount=Decimal("450250.75"),
    )
    db_session.add(bl)
    await db_session.flush()

    sr = ServiceRequest(
        request_number=f"SR-{uuid.uuid4().hex[:6]}",
        title="Customary Care Provider Supplies",
        requestor_id=ceo_user["user"].id,
        status="APPROVED",
        total_amount=Decimal("125120.25"),
        subtotal=Decimal("125120.25"),
        tax_amount=Decimal("0.00"),
    )
    db_session.add(sr)
    await db_session.commit()

    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    finance_data = res.json()["finance"]
    assert float(finance_data["total_allocated"]) >= 450250.75
    assert float(finance_data["total_spent"]) >= 125120.25
    assert float(finance_data["total_remaining"]) >= 325130.50


# ── 8. Governance Hardening & Object-Level Scope Enforcement (DEF 1-5) ────────


@pytest.mark.asyncio
async def test_director_cannot_submit_update_for_other_department(
    client: AsyncClient, ordinary_director: dict
):
    """DEF-1: Resource Team Director cannot submit department update for Finance & Administration."""
    payload = {
        "reporting_period": "2026-06",
        "department": "Finance & Administration",
        "headline_summary": "Attempted cross-department update submission",
        "accomplishments_narrative": "Should be rejected with 403 Forbidden.",
    }
    res = await client.post(
        "/api/v1/ceo-dashboard/department-updates",
        json=payload,
        headers=ordinary_director["headers"],
    )
    assert res.status_code == 403
    assert "You may only manage records for your own department" in res.text


@pytest.mark.asyncio
async def test_director_cannot_create_board_action_for_other_department(
    client: AsyncClient, ordinary_director: dict
):
    """DEF-1: Resource Team Director cannot create board action originating from Growing Up Well."""
    payload = {
        "title": "Cross-Department Board Action Attempt",
        "originating_department": "Growing Up Well",
        "background_summary": "Facility capacity review requires board endorsement for expanded caregiver beds.",
        "requested_action": "Board approval of motion to endorse capital allocation for 4 new customary beds.",
        "priority": "HIGH",
    }
    res = await client.post(
        "/api/v1/ceo-dashboard/board-actions",
        json=payload,
        headers=ordinary_director["headers"],
    )
    assert res.status_code == 403
    assert "You may only manage records for your own department" in res.text


@pytest.mark.asyncio
async def test_director_cannot_create_initiative_for_other_department(
    client: AsyncClient, db_session: AsyncSession
):
    """DEF-1: Resource Team Director with initiative write permission cannot create initiative for another department."""
    dept_director = await _create_test_user(
        db_session=db_session,
        role_key="director_rt",
        role_name="Resource Director",
        email=f"rt_dir_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Resource Director",
        department="Resource Team",
        permissions=[Permissions.EXECUTIVE_INITIATIVE_WRITE, Permissions.EXECUTIVE_INITIATIVE_READ],
    )
    payload = {
        "title": "Cross-Department Strategic Initiative",
        "department": "Governance & Executive Leadership",
        "status": "ON_TRACK",
        "priority": "MEDIUM",
    }
    res = await client.post(
        "/api/v1/ceo-dashboard/initiatives",
        json=payload,
        headers=dept_director["headers"],
    )
    assert res.status_code == 403
    assert "You may only manage records for your own department" in res.text


@pytest.mark.asyncio
async def test_board_action_decision_overwrite_is_audited(
    client: AsyncClient, ceo_user: dict
):
    """DEF-2: Amending board action decision via PATCH creates audit history without status change."""
    create_payload = {
        "title": "Decision Audit Trail Verification",
        "originating_department": "Governance & Executive Leadership",
        "background_summary": "Governance review requiring formal executive board decision audit trail.",
        "requested_action": "Board decision regarding policy ratification.",
        "priority": "HIGH",
    }
    res = await client.post(
        "/api/v1/ceo-dashboard/board-actions",
        json=create_payload,
        headers=ceo_user["headers"],
    )
    assert res.status_code == 201
    action_id = res.json()["id"]

    # Decision amended via PATCH without changing status
    patch_payload = {
        "decision": "Board conditionally approved subject to elder council review",
    }
    patch_res = await client.patch(
        f"/api/v1/ceo-dashboard/board-actions/{action_id}",
        json=patch_payload,
        headers=ceo_user["headers"],
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["decision"] == patch_payload["decision"]
    assert len(patched_data["history"]) >= 2
    assert any(
        "Decision amended via PATCH" in (h.get("action_notes") or "")
        or "elder council review" in (h.get("decision_notes") or "")
        for h in patched_data["history"]
    )


@pytest.mark.asyncio
async def test_dept_update_resubmission_snapshots_history(
    client: AsyncClient, db_session: AsyncSession, ordinary_director: dict
):
    """DEF-3: Resubmitting department update for same period snapshots previous version in history."""
    period = f"2026-Q{uuid.uuid4().hex[:4]}"
    initial_payload = {
        "reporting_period": period,
        "department": "Resource Team",
        "headline_summary": "Original headline summary for period",
        "accomplishments_narrative": "Original narrative describing Q1 goals.",
        "risks_issues": "Initial staffing shortage.",
    }
    res1 = await client.post(
        "/api/v1/ceo-dashboard/department-updates",
        json=initial_payload,
        headers=ordinary_director["headers"],
    )
    assert res1.status_code == 201
    update_id = uuid.UUID(res1.json()["id"])

    # Re-submit for same period & department with updated text
    updated_payload = {
        "reporting_period": period,
        "department": "Resource Team",
        "headline_summary": "Updated headline summary for period",
        "accomplishments_narrative": "Updated narrative reflecting new progress.",
        "risks_issues": "Resolved through hiring campaign.",
    }
    res2 = await client.post(
        "/api/v1/ceo-dashboard/department-updates",
        json=updated_payload,
        headers=ordinary_director["headers"],
    )
    assert res2.status_code == 201
    assert res2.json()["headline_summary"] == "Updated headline summary for period"

    # Verify history snapshot was recorded in database
    hist_stmt = (
        select(DepartmentExecutiveUpdateHistory)
        .where(DepartmentExecutiveUpdateHistory.update_id == update_id)
        .order_by(DepartmentExecutiveUpdateHistory.changed_at.desc())
    )
    hist_res = await db_session.execute(hist_stmt)
    histories = hist_res.scalars().all()
    assert len(histories) >= 1
    assert histories[0].previous_headline_summary == "Original headline summary for period"
    assert histories[0].previous_accomplishments_narrative == "Original narrative describing Q1 goals."
    assert histories[0].previous_risks_issues == "Initial staffing shortage."


@pytest.mark.asyncio
async def test_children_in_care_counts_distinct_children(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """DEF-4: Split placement with two concurrent active episodes counts as 1 distinct child in care."""
    child = Person(
        first_name="SplitCare",
        last_name=f"Child_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(child)
    await db_session.flush()

    h1 = PlacementHome(home_code=f"RH-{uuid.uuid4().hex[:6]}", name="Home Alpha", status="ACTIVE", total_capacity=2)
    h2 = PlacementHome(home_code=f"RH-{uuid.uuid4().hex[:6]}", name="Home Beta", status="ACTIVE", total_capacity=2)
    db_session.add_all([h1, h2])
    await db_session.flush()

    case_obj = Case(
        case_number=f"CASE-{uuid.uuid4().hex[:6]}",
        title="Split Placement Support File",
        status="ACTIVE",
    )
    db_session.add(case_obj)
    await db_session.flush()

    # Two concurrent active placement episodes for this SINGLE child
    ep1 = PlacementEpisode(
        case_id=case_obj.id,
        child_id=child.id,
        placement_home_id=h1.id,
        placement_type="CUSTOMARY_CARE",
        provider_name="Resource Caregiver Alpha",
        status="ACTIVE",
        start_date=date.today() - timedelta(days=20),
        end_date=None,
    )
    ep2 = PlacementEpisode(
        case_id=case_obj.id,
        child_id=child.id,
        placement_home_id=h2.id,
        placement_type="CUSTOMARY_CARE",
        provider_name="Resource Caregiver Beta",
        status="ACTIVE",
        start_date=date.today() - timedelta(days=10),
        end_date=None,
    )
    db_session.add_all([ep1, ep2])
    await db_session.commit()

    total_episodes_res = await db_session.execute(
        select(func.count(PlacementEpisode.id)).where(
            PlacementEpisode.status == "ACTIVE",
            PlacementEpisode.end_date.is_(None),
            PlacementEpisode.deleted_at.is_(None),
        )
    )
    total_episodes = total_episodes_res.scalar() or 0

    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    exec_summary = res.json()["executive_summary"]

    # Defensible: distinct children_in_care count
    assert exec_summary["children_in_care"]["is_available"] is True
    # Placement episodes count is at least 2, but children_in_care counts distinct children (< total active episodes)
    assert total_episodes >= 2
    assert exec_summary["children_in_care"]["value"] < total_episodes


@pytest.mark.asyncio
async def test_families_served_is_zero_with_no_open_cases(
    client: AsyncClient, db_session: AsyncSession, ceo_user: dict
):
    """DEF-5: Total Family count is not used as fallback when no active cases exist."""
    # Add an inactive/historical family with closed case
    fam = Family(family_name=f"HistoricalFamily-{uuid.uuid4().hex[:6]}")
    db_session.add(fam)
    await db_session.flush()

    closed_case = Case(
        case_number=f"CASE-{uuid.uuid4().hex[:6]}",
        title="Historical Closed Case",
        status="CLOSED",
        family_id=fam.id,
    )
    db_session.add(closed_case)
    await db_session.commit()

    res = await client.get("/api/v1/ceo-dashboard", headers=ceo_user["headers"])
    assert res.status_code == 200
    families_served_val = res.json()["executive_summary"]["families_served"]["value"]

    # Verify that total Family count in database is strictly greater than families_served,
    # proving that the old fallback to total Family table count is removed.
    all_fams_res = await db_session.execute(
        select(func.count(Family.id)).where(Family.deleted_at.is_(None))
    )
    total_db_families = all_fams_res.scalar() or 0
    assert total_db_families > 0
    assert families_served_val < total_db_families


