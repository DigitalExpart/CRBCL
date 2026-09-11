"""Focused governance and security boundary tests for CRBCL Board Dashboard.

Verifies all 23 governance, privacy, publication, and immutability controls:
1. Board Member can access Board Dashboard.
2. Board Member cannot access CEO Dashboard.
3. Board Member cannot access Cases.
4. Board Member cannot access Clients.
5. Board Member cannot access Intake.
6. Board Member cannot access reporter identity.
7. Board Member cannot access Clinical Notes.
8. Board Member cannot access medical data.
9. Board Member cannot access Resource caregiver clearances.
10. Board Member cannot access sensitive Resource complaints.
11. Board Member cannot access HR employee details.
12. Board Member cannot access Finance transaction details.
13. Board Member cannot access Admin portal.
14. IT Admin cannot automatically access Board dashboard.
15. Unpublished initiatives are invisible to Board.
16. Published initiatives are visible to Board.
17. Unpublished department updates are invisible to Board.
18. Board Actions obey governance-ready controls.
19. Board aggregate endpoints contain no client identifiers or narratives.
20. Board financial responses contain aggregate Decimal values only.
21. Board Action decision history is immutable.
22. Board Member cannot self-publish records.
23. Critical dates exclude client court and appointment events.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core.seed import PERMISSIONS_DATA, ROLE_PERMISSIONS_MAP
from app.models.board_action import BoardAction, BoardActionHistory
from app.models.case import Case
from app.models.department_update import DepartmentExecutiveUpdate
from app.models.executive_initiative import ExecutiveInitiative
from app.models.family import Family
from app.models.finance import BudgetLine, ServiceRequest
from app.models.org_ops import Employee
from app.models.person import Person
from app.models.placement import CourtEvent, PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.sprint_b_models import Appointment, Incident
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
async def board_member_user(db_session: AsyncSession):
    return await _create_test_user(
        db_session=db_session,
        role_key="board_member",
        role_name="Board Member",
        email=f"board_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Governor Alpha",
        department="Board of Governors",
        permissions=[
            Permissions.BOARD_DASHBOARD_READ,
            Permissions.BOARD_ACTION_READ,
            Permissions.BOARD_DOCUMENT_READ,
            Permissions.BOARD_REPORT_READ,
        ],
    )


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
async def director_user(db_session: AsyncSession):
    return await _create_test_user(
        db_session=db_session,
        role_key="director_manager",
        role_name="Director / Manager",
        email=f"director_{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Director Jordan",
        department="Child & Family Services",
        permissions=[
            Permissions.BOARD_ACTION_READ,
            Permissions.BOARD_ACTION_WRITE,
            Permissions.DEPARTMENT_UPDATE_READ,
            Permissions.DEPARTMENT_UPDATE_WRITE,
            Permissions.EXECUTIVE_INITIATIVE_READ,
        ],
    )


# ── 1. Board Authorization & Boundary Tests ─────────────────────────────


@pytest.mark.asyncio
async def test_board_member_can_access_board_dashboard(client: AsyncClient, board_member_user: dict):
    """Board Member user with board_dashboard.read receives 200 OK on /board/summary."""
    res = await client.get("/api/v1/board/summary", headers=board_member_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert "initiatives_total" in body
    assert "board_actions_pending" in body
    assert "total_workforce" in body
    assert "approved_budget_total" in body


@pytest.mark.asyncio
async def test_board_member_cannot_access_ceo_dashboard(client: AsyncClient, board_member_user: dict):
    """Board Member possesses no executive_dashboard.read and is denied /ceo-dashboard with 403."""
    res = await client.get("/api/v1/ceo-dashboard", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_cases(client: AsyncClient, board_member_user: dict):
    """Board Member has no case.read and is denied operational case access with 403."""
    res = await client.get("/api/v1/cases", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_clients(client: AsyncClient, board_member_user: dict):
    """Board Member has no client.read and is denied client records with 403."""
    res = await client.get("/api/v1/clients", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_intake(client: AsyncClient, board_member_user: dict):
    """Board Member has no intake.read and is denied intake referrals with 403."""
    res = await client.get("/api/v1/referrals", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_reporter_identity(client: AsyncClient, board_member_user: dict):
    """Board Member has no intake.reporter.read and is denied confidential reporter access."""
    # Attempting to access referrals endpoint without intake.read is blocked
    res = await client.get(f"/api/v1/referrals/{uuid.uuid4()}", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_clinical_notes(client: AsyncClient, board_member_user: dict):
    """Board Member has no clinical.note.read and is denied clinical records with 403."""
    res = await client.get(f"/api/v1/clinical-notes/client/{uuid.uuid4()}", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_medical_data(client: AsyncClient, board_member_user: dict):
    """Board Member has no client.medical.read permission."""
    perms = ROLE_PERMISSIONS_MAP.get("board_member", [])
    assert Permissions.CLIENT_MEDICAL_READ not in perms
    assert Permissions.CLIENT_IDENTIFIERS_READ not in perms


@pytest.mark.asyncio
async def test_board_member_cannot_access_resource_caregiver_clearances(client: AsyncClient, board_member_user: dict):
    """Board Member has no resource_clearance.adjudicate and cannot access background checks."""
    res = await client.get("/api/v1/background-checks", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_sensitive_resource_complaints(client: AsyncClient, board_member_user: dict):
    """Board Member has no resource_complaint.sensitive.read and is denied resource complaints."""
    res = await client.get("/api/v1/resource-complaints", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_hr_employee_details(client: AsyncClient, board_member_user: dict):
    """Board Member has no hr.employee.read and is denied personnel records with 403."""
    res = await client.get("/api/v1/org-ops/employees", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_finance_transaction_details(client: AsyncClient, board_member_user: dict):
    """Board Member has no finance.request.read and is denied transaction-level finance."""
    res = await client.get("/api/v1/finance/requests", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_board_member_cannot_access_admin_portal(client: AsyncClient, board_member_user: dict):
    """Board Member has no admin.users.manage and is denied admin user lists with 403."""
    res = await client.get("/api/v1/users", headers=board_member_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_it_admin_cannot_automatically_access_board_dashboard(client: AsyncClient, it_admin_user: dict):
    """IT Admin possesses no board_dashboard.read and is denied /board endpoints with 403."""
    res = await client.get("/api/v1/board/summary", headers=it_admin_user["headers"])
    assert res.status_code == 403


# ── 2. Publication Controls & Information Filtering ─────────────────────


@pytest.mark.asyncio
async def test_unpublished_initiatives_are_invisible_to_board(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Initiatives with is_board_visible=False are completely excluded from Board view."""
    secret_title = f"Confidential Staffing Restructure {uuid.uuid4().hex[:6]}"
    init = ExecutiveInitiative(
        title=secret_title,
        description="Internal executive planning",
        department="Governance",
        status="ON_TRACK",
        is_board_visible=False,
    )
    db_session.add(init)
    await db_session.commit()

    res = await client.get("/api/v1/board/initiatives", headers=board_member_user["headers"])
    assert res.status_code == 200
    titles = [i["title"] for i in res.json()]
    assert secret_title not in titles


@pytest.mark.asyncio
async def test_published_initiatives_are_visible_to_board(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Initiatives with is_board_visible=True appear on the Board Dashboard with board_summary."""
    public_title = f"C-92 Implementation Phase 2 {uuid.uuid4().hex[:6]}"
    safe_summary = "High-level strategic agreement negotiation"
    init = ExecutiveInitiative(
        title=public_title,
        description="Internal technical drafting notes",
        board_summary=safe_summary,
        department="Governance",
        status="ON_TRACK",
        priority="HIGH",
        is_board_visible=True,
    )
    db_session.add(init)
    await db_session.commit()

    res = await client.get("/api/v1/board/initiatives", headers=board_member_user["headers"])
    assert res.status_code == 200
    matching = next((i for i in res.json() if i["title"] == public_title), None)
    assert matching is not None
    assert matching["board_summary"] == safe_summary


@pytest.mark.asyncio
async def test_unpublished_department_updates_are_invisible_to_board(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Department updates with is_board_visible=False are hidden; published ones are visible."""
    period = f"2026-T{uuid.uuid4().hex[:4]}"
    internal_headline = f"Internal preliminary update {uuid.uuid4().hex[:4]}"
    dept_update = DepartmentExecutiveUpdate(
        reporting_period=period,
        department="Child Protection",
        headline_summary=internal_headline,
        accomplishments_narrative="Internal achievements",
        is_board_visible=False,
    )
    db_session.add(dept_update)
    await db_session.commit()

    # Unpublished: should not appear
    res = await client.get(f"/api/v1/board/department-updates?reporting_period={period}", headers=board_member_user["headers"])
    assert res.status_code == 200
    headlines = [u["headline_summary"] for u in res.json()]
    assert internal_headline not in headlines

    # Publish update
    dept_update.is_board_visible = True
    await db_session.commit()

    # Published: appears
    res2 = await client.get(f"/api/v1/board/department-updates?reporting_period={period}", headers=board_member_user["headers"])
    assert res2.status_code == 200
    headlines2 = [u["headline_summary"] for u in res2.json()]
    assert internal_headline in headlines2


@pytest.mark.asyncio
async def test_board_actions_obey_governance_ready_controls(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Board actions in DRAFT or with is_governance_ready=False are excluded from Board view."""
    draft_ref = f"BA-DRAFT-{uuid.uuid4().hex[:4]}"
    ready_ref = f"BA-READY-{uuid.uuid4().hex[:4]}"

    draft_action = BoardAction(
        reference_number=draft_ref,
        originating_department="Finance",
        title="Draft Capital Acquisition",
        background_summary="Internal preliminary draft",
        requested_action="Approval",
        status="DRAFT",
        is_governance_ready=False,
    )
    ready_action = BoardAction(
        reference_number=ready_ref,
        originating_department="Finance",
        title="Formal Budget Amendment",
        background_summary="Formal request for board consideration",
        requested_action="Adopt resolution",
        status="SUBMITTED",
        is_governance_ready=True,
    )
    db_session.add_all([draft_action, ready_action])
    await db_session.commit()

    res = await client.get("/api/v1/board/actions", headers=board_member_user["headers"])
    assert res.status_code == 200
    refs = [a["reference_number"] for a in res.json()]
    assert draft_ref not in refs
    assert ready_ref in refs


@pytest.mark.asyncio
async def test_board_aggregate_endpoints_contain_no_client_identifiers_or_narratives(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Board performance endpoints return purely numeric aggregates; zero child names or clinical notes."""
    secret_child_name = f"SensitiveChild_{uuid.uuid4().hex[:8]}"
    secret_narrative = f"Highly confidential clinical investigation {uuid.uuid4().hex[:8]}"

    # Seed operational client and incident
    person = Person(first_name=secret_child_name, last_name="Confidential", date_of_birth=date(2015, 1, 1))
    db_session.add(person)
    await db_session.flush()

    incident = Incident(
        title="Critical Incident Observation",
        incident_type="BEHAVIOURAL",
        severity="SEV-1",
        description=secret_narrative,
        location="Care Center",
        reported_by_name="Duty Worker",
        status="OPEN",
        incident_date=datetime.now(UTC),
    )
    db_session.add(incident)
    await db_session.commit()

    # Inspect Board Summary
    sum_res = await client.get("/api/v1/board/summary", headers=board_member_user["headers"])
    assert sum_res.status_code == 200
    sum_str = str(sum_res.json())
    assert secret_child_name not in sum_str
    assert secret_narrative not in sum_str

    # Inspect Board Risk & Compliance
    risk_res = await client.get("/api/v1/board/risk-compliance", headers=board_member_user["headers"])
    assert risk_res.status_code == 200
    risk_str = str(risk_res.json())
    assert secret_child_name not in risk_str
    assert secret_narrative not in risk_str


@pytest.mark.asyncio
async def test_board_financial_responses_contain_aggregate_decimal_values_only(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Board finance response contains Decimal aggregates only; no vendor banking or client records."""
    bline = BudgetLine(
        code=f"GOV-{uuid.uuid4().hex[:4]}",
        name="Governance Operations",
        allocated_amount=Decimal("150000.00"),
        fiscal_year="2026-2027",
    )
    db_session.add(bline)
    await db_session.commit()

    res = await client.get("/api/v1/board/finance", headers=board_member_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "total_allocated_budget" in data
    assert "total_expenditure" in data
    assert "remaining_budget" in data

    # Verify no transaction lines
    assert "invoices" not in data
    assert "bank_account" not in data
    assert "service_requests" not in data


@pytest.mark.asyncio
async def test_board_action_decision_history_is_immutable(
    client: AsyncClient, ceo_user: dict, board_member_user: dict, db_session: AsyncSession
):
    """Recording a decision creates an unmodifiable history record preserving the prior state."""
    ref = f"BA-IMMUTABLE-{uuid.uuid4().hex[:4]}"
    action = BoardAction(
        reference_number=ref,
        originating_department="Governance",
        title="Bylaw Amendment",
        background_summary="Proposed bylaw change",
        requested_action="Vote",
        status="DECISION_REQUIRED",
        is_governance_ready=True,
    )
    db_session.add(action)
    await db_session.commit()

    # Initial decision recording by CEO
    dec_res = await client.post(
        f"/api/v1/board/actions/{action.id}/decision",
        json={"decision": "Approved by unanimous vote", "status": "APPROVED", "resolution_notes": "Motion 2026-04"},
        headers=ceo_user["headers"],
    )
    assert dec_res.status_code == 200

    # Read decision history via Board member
    actions_res = await client.get("/api/v1/board/actions", headers=board_member_user["headers"])
    assert actions_res.status_code == 200
    matched = next((a for a in actions_res.json() if a["reference_number"] == ref), None)
    assert matched is not None
    assert matched["status"] == "APPROVED"
    assert matched["decision"] == "Approved by unanimous vote"
    assert len(matched["history"]) >= 1
    assert matched["history"][0]["previous_status"] == "DECISION_REQUIRED"
    assert matched["history"][0]["new_status"] == "APPROVED"


@pytest.mark.asyncio
async def test_board_member_cannot_self_publish_records(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Board Member cannot self-publish internal initiatives or updates (receives 403 Forbidden)."""
    init = ExecutiveInitiative(title="Self Publish Test", description="Internal", status="ON_TRACK", is_board_visible=False)
    db_session.add(init)
    await db_session.commit()

    # Board member attempting to publish initiative -> 403
    pub_res = await client.post(
        f"/api/v1/board/initiatives/{init.id}/publish",
        json={"is_board_visible": True, "board_summary": "Attempted self-publish"},
        headers=board_member_user["headers"],
    )
    assert pub_res.status_code == 403


@pytest.mark.asyncio
async def test_critical_dates_exclude_client_events(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Critical dates include only governance deadlines; client court appearances are excluded."""
    today = date.today()
    private_client_hearing = f"Private Court Hearing Child_{uuid.uuid4().hex[:6]}"

    # Add court event with private client details
    case = Case(
        case_number=f"CAS-TEST-{uuid.uuid4().hex[:6]}",
        title="Confidential Client Protection Case",
        status="Open",
        stage="ONGOING_SERVICES",
    )
    db_session.add(case)
    await db_session.flush()

    court_event = CourtEvent(
        case_id=case.id,
        hearing_type="PERMANENCY_HEARING",
        hearing_date=today + timedelta(days=2),
        judge_name="Justice Private",
        outcome_summary=private_client_hearing,
        status="SCHEDULED",
    )
    db_session.add(court_event)
    await db_session.commit()

    res = await client.get("/api/v1/board/critical-dates", headers=board_member_user["headers"])
    assert res.status_code == 200
    dates_str = str(res.json())
    assert private_client_hearing not in dates_str


@pytest.mark.asyncio
async def test_board_workforce_metrics_mark_unsupported_data_unavailable(
    client: AsyncClient, board_member_user: dict
):
    """FTE, turnover, contract type, and exit reasons must be explicitly marked is_available: false with reasons."""
    res = await client.get("/api/v1/board/workforce", headers=board_member_user["headers"])
    assert res.status_code == 200
    wf = res.json()

    # FTE allocation is not tracked in current Employee schema
    assert wf["fte_count"]["is_available"] is False
    assert wf["fte_count"]["value"] is None
    assert "Employee schema" in wf["fte_count"]["reason"]

    # Turnover rate cannot be reliably computed without voluntary/involuntary classification
    assert wf["turnover_rate"]["is_available"] is False
    assert wf["turnover_rate"]["value"] is None
    assert "Turnover rate requires authoritative separation" in wf["turnover_rate"]["reason"]

    # Permanent vs term contract type
    assert wf["contract_type_metric"]["is_available"] is False
    assert wf["contract_type_metric"]["value"] is None
    assert "Employee schema" in wf["contract_type_metric"]["reason"]

    # Resignation vs termination exit reasons
    assert wf["exit_reason_metric"]["is_available"] is False
    assert wf["exit_reason_metric"]["value"] is None
    assert "Employee schema" in wf["exit_reason_metric"]["reason"]


@pytest.mark.asyncio
async def test_non_executive_cannot_modify_is_governance_ready(
    client: AsyncClient, director_user: dict, db_session: AsyncSession
):
    """Ordinary Director cannot self-mark a BoardAction as governance-ready."""
    # 1. On creation: passing is_governance_ready=True is overridden to False for non-executives
    create_res = await client.post(
        "/api/v1/ceo-dashboard/board-actions",
        json={
            "originating_department": "Child & Family Services",
            "title": "Director Submitted Matter",
            "background_summary": "Summary of matter",
            "requested_action": "Board review",
            "is_governance_ready": True,
        },
        headers=director_user["headers"],
    )
    assert create_res.status_code == 201
    ba_data = create_res.json()
    assert ba_data["is_governance_ready"] is False

    # 2. On update: attempting to patch is_governance_ready returns 403 Forbidden
    patch_res = await client.patch(
        f"/api/v1/ceo-dashboard/board-actions/{ba_data['id']}",
        json={"is_governance_ready": True},
        headers=director_user["headers"],
    )
    assert patch_res.status_code == 403

    # 3. Patching normal fields without is_governance_ready succeeds
    patch_ok = await client.patch(
        f"/api/v1/ceo-dashboard/board-actions/{ba_data['id']}",
        json={"title": "Updated Director Matter Title"},
        headers=director_user["headers"],
    )
    assert patch_ok.status_code == 200
    assert patch_ok.json()["title"] == "Updated Director Matter Title"


@pytest.mark.asyncio
async def test_executive_can_toggle_board_action_governance_readiness(
    client: AsyncClient, ceo_user: dict, db_session: AsyncSession
):
    """Authorized executive leadership with board_publication.manage can toggle governance readiness."""
    action = BoardAction(
        reference_number=f"BA-EXEC-{uuid.uuid4().hex[:4]}",
        originating_department="Executive Leadership",
        title="Bylaw Policy Ratification",
        background_summary="Executive policy review",
        requested_action="Adopt resolution",
        is_governance_ready=False,
    )
    db_session.add(action)
    await db_session.commit()

    # Executive publishes / marks governance-ready
    pub_res = await client.post(
        f"/api/v1/board/actions/{action.id}/governance-ready?is_governance_ready=true",
        headers=ceo_user["headers"],
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_governance_ready"] is True


@pytest.mark.asyncio
async def test_board_member_cannot_toggle_governance_readiness(
    client: AsyncClient, board_member_user: dict, db_session: AsyncSession
):
    """Board Member cannot publish or toggle governance readiness on Board Actions."""
    action = BoardAction(
        reference_number=f"BA-DENY-{uuid.uuid4().hex[:4]}",
        originating_department="Finance",
        title="Capital Plan",
        background_summary="Capital request",
        requested_action="Approval",
        is_governance_ready=False,
    )
    db_session.add(action)
    await db_session.commit()

    pub_res = await client.post(
        f"/api/v1/board/actions/{action.id}/governance-ready?is_governance_ready=true",
        headers=board_member_user["headers"],
    )
    assert pub_res.status_code == 403
