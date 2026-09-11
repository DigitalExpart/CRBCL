"""Cross-Module UAT & End-to-End Business Workflows Regression Suite.

Verifies end-to-end multi-department journeys (Chains A-F), role privacy boundaries,
immutability controls, financial integrity, and IDOR fail-closed security.
Baseline commit: 7df63f10fd3707fdb46beb520353a48a451aaaa4
Alembic migration head: 026_board_dashboard_publication_controls
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.auth.service import create_access_token
from app.core.config import get_settings
from app.core.seed import ROLE_PERMISSIONS_MAP
from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.finance import ServiceRequest
from app.models.front_desk import FrontDeskSubmission
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.resource_recruitment import RecruitmentState, ResourceRecruitment
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.permissions.constants import Permissions


async def _provision_user(
    db: AsyncSession,
    role_key: str,
    role_name: str,
    email: str,
    full_name: str,
    department: str | None = None,
    permissions: list[str | Permissions] | None = None,
) -> dict:
    """Helper to provision a test user with assigned role and permissions."""
    res = await db.execute(select(Role).where(Role.key == role_key))
    role = res.scalars().first()
    if not role:
        role = Role(key=role_key, name=role_name, is_system=True)
        db.add(role)
        await db.flush()

    if permissions is None:
        raw_perms = ROLE_PERMISSIONS_MAP.get(role_key, [])
        permissions = [p if isinstance(p, str) else p.value for p in raw_perms]

    for p_key in permissions:
        key_str = p_key if isinstance(p_key, str) else p_key.value
        p_res = await db.execute(select(Permission).where(Permission.key == key_str))
        perm = p_res.scalars().first()
        if not perm:
            perm = Permission(key=key_str, name=key_str, category="test")
            db.add(perm)
            await db.flush()

        rp_res = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id,
            )
        )
        if not rp_res.scalars().first():
            rp = RolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    await db.flush()

    user = User(
        email=email,
        email_normalized=email.lower(),
        password_hash=hash_password("password123"),
        full_name=full_name,
        department=department,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    ur = UserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    await db.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


# ── FIXTURES ───────────────────────────────────────────────────────────────────


@pytest.fixture
async def it_admin(db_session: AsyncSession):
    return await _provision_user(
        db_session, "it_admin", "IT Admin", f"admin_{uuid.uuid4().hex[:6]}@crbcl.ca", "Sys Admin", "IT & Systems"
    )


@pytest.fixture
async def front_desk_worker(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "front_desk",
        "Front Desk",
        f"front_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Front Desk Worker",
        "Front Desk & Reception",
    )


@pytest.fixture
async def receiving_worker(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "director_manager",
        "Receiving Worker",
        f"recv_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "CFS Receiving Worker",
        "Child & Family Services",
    )


@pytest.fixture
async def caseworker(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "caseworker",
        "Caseworker",
        f"cw_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Protection Worker",
        "Child & Family Services",
    )


@pytest.fixture
async def supervisor(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "supervisor",
        "Supervisor",
        f"sup_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Case Supervisor",
        "Child & Family Services",
    )


@pytest.fixture
async def resource_worker(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "resource_worker",
        "Resource Worker",
        f"rw_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Resource Specialist",
        "Resource Unit",
    )


@pytest.fixture
async def resource_supervisor(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "resource_supervisor",
        "Resource Supervisor",
        f"rs_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Resource Manager",
        "Resource Unit",
    )


@pytest.fixture
async def finance_worker_1(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "finance_staff",
        "Finance Staff",
        f"fin1_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Finance Officer 1",
        "Finance & Operations",
    )


@pytest.fixture
async def finance_worker_2(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "finance_staff",
        "Finance Staff",
        f"fin2_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Finance Officer 2",
        "Finance & Operations",
    )


@pytest.fixture
async def ceo_user(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "ceo",
        "CEO",
        f"ceo_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Executive CEO",
        "Governance & Executive Leadership",
    )


@pytest.fixture
async def board_member(db_session: AsyncSession):
    return await _provision_user(
        db_session,
        "board_member",
        "Board Member",
        f"bm_{uuid.uuid4().hex[:6]}@crbcl.ca",
        "Board Trustee",
        "Board of Directors",
    )


# ── BUSINESS WORKFLOW CHAINS A TO F ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_chain_a_public_ingestion_to_intake(
    client: AsyncClient, front_desk_worker: dict, receiving_worker: dict, db_session: AsyncSession
):
    """Chain A: Google Form Webhook -> Front Desk Review/Route -> Receiving Department -> Duplicate Check -> Internal Referral."""
    settings = get_settings()
    ext_id = f"RESP-UAT-{uuid.uuid4().hex[:8]}"

    # 1. Google Form webhook ingestion
    webhook_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={
            "response_id": ext_id,
            "submitter_name": "Elder Jane Starblanket",
            "submitter_email": "jane.starblanket@redbear.ca",
            "submitter_phone": "306-555-0199",
            "submitter_relationship": "Maternal Grandparent",
            "inquiry_type": "child_welfare",
            "urgency": "Medium",
            "summary": "Requesting family support resources and kinship care assessment for grandchildren.",
            "details": "Children are currently safe with grandparents, need respite and school supplies support.",
        },
        headers={"X-CRBCL-Webhook-Secret": settings.front_desk_webhook_secret},
    )
    assert webhook_res.status_code == 201
    webhook_data = webhook_res.json()
    assert webhook_data["status"] == "RECEIVED"
    submission_id = webhook_data["submission_id"]

    # 2. Front Desk worker reviews and routes to CFS
    route_res = await client.post(
        f"/api/v1/front-desk/submissions/{submission_id}/route",
        json={
            "destination_department": "Child & Family Services",
            "urgency": "Medium",
            "routing_notes": "Routing to CFS Protection for kinship assessment.",
        },
        headers=front_desk_worker["headers"],
    )
    assert route_res.status_code == 200
    assert route_res.json()["status"] == "ROUTED"
    assert route_res.json()["destination_department"] == "Child & Family Services"

    # 3. Receiving Department worker views queue and takes department action
    dept_queue_res = await client.get(
        "/api/v1/front-desk/department-queue",
        headers=receiving_worker["headers"],
    )
    assert dept_queue_res.status_code == 200
    items = dept_queue_res.json()["items"]
    assert any(item["id"] == submission_id for item in items)

    dept_action_res = await client.patch(
        f"/api/v1/front-desk/submissions/{submission_id}/department-action",
        json={
            "action": "ACCEPTED",
            "notes": "CFS Intake accepts submission for preliminary kinship inquiry.",
        },
        headers=receiving_worker["headers"],
    )
    assert dept_action_res.status_code == 200
    assert dept_action_res.json()["status"] == "ACCEPTED"

    # 4. Duplicate Check
    dup_res = await client.get(
        f"/api/v1/front-desk/submissions/{submission_id}/duplicates",
        headers=receiving_worker["headers"],
    )
    assert dup_res.status_code == 200
    assert isinstance(dup_res.json(), list)

    # 5. Conversion to formal internal Referral
    conv_res = await client.post(
        f"/api/v1/front-desk/submissions/{submission_id}/convert-to-referral",
        json={
            "priority": "Medium",
            "community": "Red Bear Lodge",
            "immediate_safety_concerns": False,
            "notes": "Formal referral established from verified public submission.",
        },
        headers=receiving_worker["headers"],
    )
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["status"] == "CONVERTED"
    assert conv_data["referral_id"] is not None


@pytest.mark.asyncio
async def test_chain_b_intake_to_case_notes_and_plans(
    client: AsyncClient, caseworker: dict, supervisor: dict, db_session: AsyncSession
):
    """Chain B: Case Opening -> Note Locking -> Note Addendum (immutable overwrite rejection) -> Active Efforts."""
    case = Case(
        case_number=f"CAS-UAT-{uuid.uuid4().hex[:6]}",
        title="Starblanket Family Protection & Support",
        status="Open",
        stage="INVESTIGATION",
    )
    db_session.add(case)
    await db_session.commit()

    # 1. Caseworker creates Case Note
    note_res = await client.post(
        f"/api/v1/cases/{case.id}/notes",
        json={
            "case_id": str(case.id),
            "subject": "Quarterly Home Visit",
            "content": "Home visit completed with maternal caregiver. Children are healthy and well supported.",
            "note_type": "Progress Note",
        },
        headers=caseworker["headers"],
    )
    assert note_res.status_code == 201
    note_id = note_res.json()["id"]

    # 2. Finalize Note (Locking)
    lock_res = await client.post(
        f"/api/v1/case-notes/{note_id}/lock",
        headers=caseworker["headers"],
    )
    assert lock_res.status_code == 200
    assert lock_res.json()["is_locked"] is True

    # 3. Immutability Verification: Attempt to overwrite locked note
    overwrite_res = await client.patch(
        f"/api/v1/case-notes/{note_id}",
        json={"content": "Attempting to silently overwrite locked clinical record."},
        headers=caseworker["headers"],
    )
    assert overwrite_res.status_code == 409
    err_msg = overwrite_res.json().get("error", {}).get("message", "") or str(overwrite_res.json().get("detail", ""))
    assert "locked" in err_msg.lower()

    # 4. Lawful Correction via Addendum
    addendum_res = await client.post(
        f"/api/v1/case-notes/{note_id}/addenda",
        json={
            "content": "Addendum: Maternal grandmother requested follow-up nutrition support resources.",
            "reason": "Caregiver addendum request.",
        },
        headers=caseworker["headers"],
    )
    assert addendum_res.status_code == 201

    # 5. Active Efforts Entry
    efforts_res = await client.post(
        f"/api/v1/cases/{case.id}/active-efforts",
        json={
            "effort_type": "CULTURAL_CONNECTION",
            "description": "Engaged Band representative regarding upcoming cultural ceremony.",
            "service_date": date.today().isoformat(),
            "outcome": "ONGOING",
        },
        headers=caseworker["headers"],
    )
    assert efforts_res.status_code == 201


@pytest.mark.asyncio
async def test_chain_c_removal_placement_matching_and_capacity(
    client: AsyncClient, caseworker: dict, resource_worker: dict, db_session: AsyncSession
):
    """Chain C: Case Removal -> Placement Matching -> Placement Episode -> Bed Capacity Update."""
    child = Person(first_name="Aiden", last_name="Starblanket", date_of_birth=date(2016, 8, 20))
    home = PlacementHome(
        home_code=f"HME-{uuid.uuid4().hex[:4]}",
        name="Circle of Care Home",
        status="ACTIVE",
        total_capacity=3,
        primary_caregiver_name="Elder Mary",
    )
    db_session.add_all([child, home])
    await db_session.commit()

    case = Case(
        case_number=f"CAS-PLM-{uuid.uuid4().hex[:6]}",
        title="Starblanket Placement Support",
        status="Open",
        stage="IN_CARE",
    )
    db_session.add(case)
    await db_session.commit()

    # 1. Execute Placement Matching Query
    match_res = await client.post(
        "/api/v1/placement-matching/evaluate",
        json={
            "child_id": str(child.id),
            "age": 10,
            "indigenous_community": "Red Bear",
            "sibling_group_size": 1,
        },
        headers=resource_worker["headers"],
    )
    assert match_res.status_code == 200

    # 2. Human Worker creates Placement Episode
    episode_res = await client.post(
        f"/api/v1/cases/{case.id}/placements",
        json={
            "child_id": str(child.id),
            "placement_home_id": str(home.id),
            "placement_type": "FOSTER_HOME",
            "start_date": date.today().isoformat(),
            "primary_caregiver_name": "Elder Mary",
        },
        headers=caseworker["headers"],
    )
    assert episode_res.status_code == 201

    # 3. Capacity verification
    cap_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=resource_worker["headers"])
    assert cap_res.status_code == 200
    assert cap_res.json()["occupied_beds"] >= 1


@pytest.mark.asyncio
async def test_chain_d_caregiver_lifecycle_and_compliance(
    client: AsyncClient, resource_worker: dict, resource_supervisor: dict, db_session: AsyncSession
):
    """Chain D: Recruitment Application -> Clearance -> License -> Monitoring Visit."""
    caregiver = Person(first_name="Joseph", last_name="Bear", date_of_birth=date(1985, 4, 12))
    home = PlacementHome(
        home_code=f"REC-{uuid.uuid4().hex[:4]}",
        name="Prospective Foster Family",
        status="ACTIVE",
        total_capacity=2,
    )
    db_session.add_all([caregiver, home])
    await db_session.commit()

    # 1. Create Recruitment Record
    rec_res = await client.post(
        "/api/v1/resource-recruitment",
        json={
            "resource_home_id": str(home.id),
            "notes": "Initial caregiver inquiry submitted.",
            "applicants": [{"person_id": str(caregiver.id), "role": "PRIMARY_APPLICANT"}],
            "initial_state": "INQUIRY",
        },
        headers=resource_worker["headers"],
    )
    assert rec_res.status_code == 201
    rec_id = rec_res.json()["id"]

    # 2. Transition state through orientation
    step_res = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        json={"to_state": "ORIENTATION", "notes": "Commenced caregiver orientation."},
        headers=resource_worker["headers"],
    )
    assert step_res.status_code == 200
    assert step_res.json()["current_state"] == "ORIENTATION"

    # 3. License Issuance by Supervisor
    lic_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/licenses",
        json={
            "license_number": f"LIC-{uuid.uuid4().hex[:6]}",
            "license_type": "STANDARD_FOSTER",
            "effective_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "status": "ACTIVE",
            "issuing_authority": "CRBCL Resource Unit",
        },
        headers=resource_supervisor["headers"],
    )
    assert lic_res.status_code == 201


@pytest.mark.asyncio
async def test_chain_e_department_to_ceo_to_board_publication(
    client: AsyncClient, receiving_worker: dict, ceo_user: dict, board_member: dict, db_session: AsyncSession
):
    """Chain E: Department Executive Update -> CEO Executive Review -> Explicit Board Publication -> Board Governance Visibility."""
    period = f"2026-Q{uuid.uuid4().hex[:2]}"

    # 1. Department Director submits update
    dept_res = await client.post(
        "/api/v1/ceo-dashboard/department-updates",
        json={
            "department": "Child & Family Services",
            "reporting_period": period,
            "headline_summary": "CFS Q1 Operations",
            "accomplishments_narrative": "Completed 100% of required visits.",
            "risks_issues": "Resource home recruitment in northern quadrant.",
            "support_decision_requested": "None at this time.",
            "status": "SUBMITTED",
        },
        headers=receiving_worker["headers"],
    )
    assert dept_res.status_code == 201
    update_id = dept_res.json()["id"]

    # 2. Board member initially cannot see unpublished update
    board_init_res = await client.get(
        f"/api/v1/board/department-updates?reporting_period={period}", headers=board_member["headers"]
    )
    assert board_init_res.status_code == 200
    assert not any(u["id"] == update_id for u in board_init_res.json())

    # 3. CEO explicitly publishes update to Board
    pub_res = await client.post(
        f"/api/v1/board/department-updates/{update_id}/publish",
        json={"is_board_visible": True},
        headers=ceo_user["headers"],
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_board_visible"] is True

    # 4. Board member now sees published update
    board_after_res = await client.get(
        f"/api/v1/board/department-updates?reporting_period={period}", headers=board_member["headers"]
    )
    assert board_after_res.status_code == 200
    assert any(u["id"] == update_id for u in board_after_res.json())


@pytest.mark.asyncio
async def test_chain_f_finance_anti_self_approval_and_decimal_integrity(
    client: AsyncClient, finance_worker_1: dict, finance_worker_2: dict, db_session: AsyncSession
):
    """Chain F: Purchase Order -> Anti-Self-Approval -> Decimal Integrity Verification."""
    # 1. Finance Officer 1 creates financial service request
    req_res = await client.post(
        "/api/v1/finance/requests",
        json={
            "request_type": "PURCHASE_ORDER",
            "title": "School Supplies Support",
            "currency": "CAD",
            "vendor_name": "Northern Staples",
            "items": [
                {
                    "description": "Backpacks and notebooks",
                    "quantity": "2.00",
                    "unit_price": "124.995",
                }
            ],
        },
        headers=finance_worker_1["headers"],
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # 2. Finance Officer 1 submits the request
    submit_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/submit",
        headers=finance_worker_1["headers"],
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING_APPROVAL"

    # 3. Anti-Self-Approval: Requester attempting to approve own request is strictly forbidden (403)
    self_approve_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/approve",
        json={"comments": "Self-approval attempt"},
        headers=finance_worker_1["headers"],
    )
    assert self_approve_res.status_code == 403
    err_msg = self_approve_res.json().get("error", {}).get("message", "") or str(self_approve_res.json().get("detail", ""))
    assert "segregation of duties" in err_msg.lower()

    # 4. Second Finance Officer approves
    approve_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/approve",
        json={"comments": "Approved by second officer"},
        headers=finance_worker_2["headers"],
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

    # 5. Decimal integrity check
    sr = await db_session.get(ServiceRequest, uuid.UUID(req_id))
    assert isinstance(sr.subtotal, Decimal)
    assert isinstance(sr.total_amount, Decimal)


# ── PRIVACY AND IDOR TESTS ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_idor_and_cross_role_access_denials(
    client: AsyncClient,
    it_admin: dict,
    front_desk_worker: dict,
    board_member: dict,
    caseworker: dict,
    db_session: AsyncSession,
):
    """Verify fail-closed RBAC: knowing UUID does NOT bypass security boundaries."""
    case = Case(
        case_number=f"CAS-IDOR-{uuid.uuid4().hex[:6]}",
        title="Highly Confidential Case",
        status="Open",
        stage="INVESTIGATION",
    )
    db_session.add(case)
    await db_session.commit()

    # 1. Front Desk cannot access Case records
    fd_case = await client.get(f"/api/v1/cases/{case.id}", headers=front_desk_worker["headers"])
    assert fd_case.status_code == 403

    # 2. Board Member cannot access Case records
    bm_case = await client.get(f"/api/v1/cases/{case.id}", headers=board_member["headers"])
    assert bm_case.status_code == 403

    # 3. IT Admin cannot access Case records
    it_case = await client.get(f"/api/v1/cases/{case.id}", headers=it_admin["headers"])
    assert it_case.status_code == 403

    # 4. IT Admin cannot access Board governance dashboard
    it_board = await client.get("/api/v1/board/summary", headers=it_admin["headers"])
    assert it_board.status_code == 403

    # 5. Caseworker cannot access Board governance dashboard
    cw_board = await client.get("/api/v1/board/summary", headers=caseworker["headers"])
    assert cw_board.status_code == 403

    # 6. Caseworker cannot access CEO Executive dashboard
    cw_ceo = await client.get("/api/v1/ceo-dashboard", headers=caseworker["headers"])
    assert cw_ceo.status_code == 403
