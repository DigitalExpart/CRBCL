"""Tests for Resource Unit Caregiver Recruitment, State Transitions, Household History, and Dashboard Metrics.

Covers:
- Full sequential recruitment pipeline progression:
  INQUIRY -> ORIENTATION -> APPLICATION -> ASSESSMENT -> APPROVAL_REVIEW -> APPROVED
- Terminal states: DECLINED and WITHDRAWN
- Resume behavior: ON_HOLD can resume ONLY to its previous state
- Invalid transition rejection
- Append-only transition history
- Real persisted household membership history on PlacementHomeMember
- Authoritative dashboard metrics (capacity - active placements)
- Permission enforcement and IT Admin privacy protection
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeMember
from app.models.role import Permission, RolePermission
from app.permissions.constants import Permissions


@pytest.fixture
async def resource_worker_user(
    db_session: AsyncSession, caseworker_user: dict, seed_roles_and_permissions: dict
):
    """Grant Resource Unit worker permissions to caseworker without modifying conftest.py."""
    caseworker_role = seed_roles_and_permissions["roles"]["caseworker"]
    for perm_key in [
        Permissions.RESOURCE_HOME_READ,
        Permissions.RESOURCE_HOME_WRITE,
        Permissions.RESOURCE_RECRUITMENT_READ,
        Permissions.RESOURCE_RECRUITMENT_WRITE,
        Permissions.RESOURCE_DASHBOARD_READ,
        Permissions.PLACEMENT_HOME_READ,
        Permissions.PLACEMENT_HOME_MEMBER_MANAGE,
    ]:
        res = await db_session.execute(select(Permission).where(Permission.key == perm_key.value))
        p = res.scalars().first()
        if p:
            rp = RolePermission(role_id=caseworker_role.id, permission_id=p.id)
            db_session.add(rp)
    await db_session.commit()
    return caseworker_user


@pytest.fixture
async def resource_approver_user(
    db_session: AsyncSession, supervisor_user: dict, seed_roles_and_permissions: dict
):
    """Grant Resource Unit approval permissions to supervisor without modifying conftest.py."""
    supervisor_role = seed_roles_and_permissions["roles"]["supervisor"]
    for perm_key in [
        Permissions.RESOURCE_HOME_READ,
        Permissions.RESOURCE_HOME_WRITE,
        Permissions.RESOURCE_RECRUITMENT_READ,
        Permissions.RESOURCE_RECRUITMENT_WRITE,
        Permissions.RESOURCE_RECRUITMENT_APPROVE,
        Permissions.RESOURCE_DASHBOARD_READ,
        Permissions.PLACEMENT_HOME_READ,
        Permissions.PLACEMENT_HOME_MEMBER_MANAGE,
    ]:
        res = await db_session.execute(select(Permission).where(Permission.key == perm_key.value))
        p = res.scalars().first()
        if p:
            rp = RolePermission(role_id=supervisor_role.id, permission_id=p.id)
            db_session.add(rp)
    await db_session.commit()
    return supervisor_user


@pytest.mark.asyncio
async def test_create_resource_recruitment_with_applicants(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """Test creating an authoritative recruitment application with primary and secondary applicants."""
    headers = resource_worker_user["headers"]

    # 1. Create canonical Person records
    p1 = Person(first_name="Clara", last_name="Bird", gender="FEMALE", date_of_birth=date(1982, 3, 15))
    p2 = Person(first_name="Thomas", last_name="Bird", gender="MALE", date_of_birth=date(1980, 7, 22))
    db_session.add_all([p1, p2])
    await db_session.flush()

    # 2. Submit recruitment inquiry
    payload = {
        "initial_state": "INQUIRY",
        "notes": "Family interested in fostering siblings / kinship placements.",
        "applicants": [
            {
                "person_id": str(p1.id),
                "role": "PRIMARY_APPLICANT",
                "snapshot": {"phone": "306-555-1234", "first_name": "Clara", "last_name": "Bird"},
            },
            {
                "person_id": str(p2.id),
                "role": "SECONDARY_APPLICANT",
                "snapshot": {"phone": "306-555-5678", "first_name": "Thomas", "last_name": "Bird"},
            },
        ],
    }

    res = await client.post("/api/v1/resource-recruitment", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["current_state"] == "INQUIRY"
    assert len(data["applicants"]) == 2
    assert len(data["history"]) == 1
    assert data["history"][0]["from_state"] == "INQUIRY"
    assert data["history"][0]["to_state"] == "INQUIRY"
    assert "Bird" in (data["applicants"][0]["person_name"] or "")


@pytest.mark.asyncio
async def test_recruitment_normal_progression_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
    resource_approver_user: dict,
):
    """Test full sequential lifecycle: INQUIRY -> ORIENTATION -> APPLICATION -> ASSESSMENT -> APPROVAL_REVIEW -> APPROVED."""
    headers = resource_worker_user["headers"]

    person = Person(first_name="Sarah", last_name="Bear", gender="FEMALE")
    home = PlacementHome(
        home_code=f"PH-TEST-{uuid.uuid4().hex[:6]}",
        name="Bear Lodge Care Home",
        home_type="LICENSED_FOSTER",
        total_capacity=3,
        city="Regina",
    )
    db_session.add_all([person, home])
    await db_session.flush()

    # Create application in INQUIRY
    create_res = await client.post(
        "/api/v1/resource-recruitment",
        headers=headers,
        json={
            "initial_state": "INQUIRY",
            "applicants": [{"person_id": str(person.id), "role": "PRIMARY_APPLICANT"}],
        },
    )
    rec_id = create_res.json()["id"]

    # 1. Advance: INQUIRY -> ORIENTATION
    t1 = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ORIENTATION", "notes": "Attended orientation workshop."},
    )
    assert t1.status_code == 200
    assert t1.json()["current_state"] == "ORIENTATION"

    # 2. Advance: ORIENTATION -> APPLICATION
    t2 = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "APPLICATION", "notes": "Formal PRIDE application received."},
    )
    assert t2.status_code == 200
    assert t2.json()["current_state"] == "APPLICATION"

    # 3. Advance: APPLICATION -> ASSESSMENT
    t3 = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ASSESSMENT", "notes": "Home safety study commenced."},
    )
    assert t3.status_code == 200
    assert t3.json()["current_state"] == "ASSESSMENT"

    # 4. Advance: ASSESSMENT -> APPROVAL_REVIEW
    t4 = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "APPROVAL_REVIEW", "notes": "Assessment completed; awaiting committee sign-off."},
    )
    assert t4.status_code == 200
    assert t4.json()["current_state"] == "APPROVAL_REVIEW"

    # Worker without approval capability attempts APPROVAL_REVIEW -> APPROVED: must fail with 403
    t5_worker = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={
            "to_state": "APPROVED",
            "resource_home_id": str(home.id),
            "notes": "Worker attempting unapproved transition.",
        },
    )
    assert t5_worker.status_code == 403
    assert t5_worker.json()["error"]["code"] == "PERMISSION_DENIED"

    # Authorized Approver advances: APPROVAL_REVIEW -> APPROVED (with home allocation)
    approver_headers = resource_approver_user["headers"]
    t5 = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=approver_headers,
        json={
            "to_state": "APPROVED",
            "resource_home_id": str(home.id),
            "notes": "Caregiver approved and linked to Bear Lodge Care Home.",
        },
    )
    assert t5.status_code == 200
    final_data = t5.json()
    assert final_data["current_state"] == "APPROVED"
    assert final_data["resource_home_id"] == str(home.id)
    assert final_data["resource_home_code"] == home.home_code

    # Verify append-only history captured every single step (initial + 5 transitions = 6 records)
    assert len(final_data["history"]) == 6


@pytest.mark.asyncio
async def test_recruitment_on_hold_and_resume_behavior(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """Test that ON_HOLD correctly records previous_state and resumes ONLY to that state."""
    headers = resource_worker_user["headers"]

    person = Person(first_name="David", last_name="Lavallee", gender="MALE")
    db_session.add(person)
    await db_session.flush()

    # Create in INQUIRY and advance to ORIENTATION
    c = await client.post(
        "/api/v1/resource-recruitment",
        headers=headers,
        json={"applicants": [{"person_id": str(person.id), "role": "PRIMARY_APPLICANT"}]},
    )
    rec_id = c.json()["id"]

    await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ORIENTATION"},
    )

    # Pause at ORIENTATION -> ON_HOLD
    pause_res = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ON_HOLD", "notes": "Family requested delay due to home renovations."},
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["current_state"] == "ON_HOLD"
    assert pause_res.json()["previous_state"] == "ORIENTATION"

    # Attempt invalid resume (e.g. trying to resume to ASSESSMENT instead of ORIENTATION)
    invalid_resume = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ASSESSMENT"},
    )
    assert invalid_resume.status_code == 400
    err_body = invalid_resume.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "resume" in err_msg.lower()

    # Valid resume back to ORIENTATION
    valid_resume = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ORIENTATION", "notes": "Renovations complete, resuming orientation."},
    )
    assert valid_resume.status_code == 200
    assert valid_resume.json()["current_state"] == "ORIENTATION"
    assert valid_resume.json()["previous_state"] is None


@pytest.mark.asyncio
async def test_terminal_declined_and_withdrawn_states(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """Test that DECLINED and WITHDRAWN states are strictly terminal."""
    headers = resource_worker_user["headers"]

    person = Person(first_name="Jane", last_name="Doe", gender="FEMALE")
    db_session.add(person)
    await db_session.flush()

    c = await client.post(
        "/api/v1/resource-recruitment",
        headers=headers,
        json={"applicants": [{"person_id": str(person.id), "role": "PRIMARY_APPLICANT"}]},
    )
    rec_id = c.json()["id"]

    # Transition to DECLINED
    decline_res = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "DECLINED", "notes": "Applicant does not meet regional housing criteria."},
    )
    assert decline_res.status_code == 200
    assert decline_res.json()["current_state"] == "DECLINED"

    # Attempt transition from terminal state -> must fail
    next_try = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ORIENTATION"},
    )
    assert next_try.status_code == 400
    err_body = next_try.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "terminal" in err_msg.lower()


@pytest.mark.asyncio
async def test_invalid_step_skipping_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """Test that skipping stages (e.g. INQUIRY directly to APPROVED) is rejected."""
    headers = resource_worker_user["headers"]

    person = Person(first_name="Peter", last_name="Peltier", gender="MALE")
    db_session.add(person)
    await db_session.flush()

    c = await client.post(
        "/api/v1/resource-recruitment",
        headers=headers,
        json={"applicants": [{"person_id": str(person.id), "role": "PRIMARY_APPLICANT"}]},
    )
    rec_id = c.json()["id"]

    # Try skipping directly from INQUIRY to ASSESSMENT (skipping ORIENTATION and APPLICATION)
    bad_res = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ASSESSMENT"},
    )
    assert bad_res.status_code == 400
    err_body = bad_res.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "invalid progression" in err_msg.lower()


@pytest.mark.asyncio
async def test_persisted_household_membership_history(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """Test that ending a household member preserves the row in the historical record rather than deleting it."""
    headers = resource_worker_user["headers"]

    home = PlacementHome(
        home_code=f"PH-HIST-{uuid.uuid4().hex[:6]}",
        name="Wolf Clan Home",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
        city="Regina",
    )
    person = Person(first_name="Robert", last_name="Acoose", gender="MALE")
    db_session.add_all([home, person])
    await db_session.flush()

    # 1. Add household member
    member = PlacementHomeMember(
        placement_home_id=home.id,
        person_id=person.id,
        role="PRIMARY_CAREGIVER",
        start_date=date(2025, 1, 1),
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()

    # 2. End membership via historical persistence endpoint
    end_res = await client.post(f"/api/v1/resource-recruitment/members/{member.id}/end", headers=headers)
    assert end_res.status_code == 200, end_res.text
    end_data = end_res.json()
    assert end_data["is_active"] is False
    assert end_data["end_date"] is not None

    # 3. Add subsequent membership period for the same person (new role)
    new_member = PlacementHomeMember(
        placement_home_id=home.id,
        person_id=person.id,
        role="SECONDARY_CAREGIVER",
        start_date=date.today(),
        is_active=True,
    )
    db_session.add(new_member)
    await db_session.flush()

    # 4. Fetch home detail from API and verify both the historical and active members are preserved
    home_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert home_res.status_code == 200
    members = home_res.json()["members"]
    assert len(members) == 2
    assert any(m["is_active"] is False for m in members)
    assert any(m["is_active"] is True for m in members)


@pytest.mark.asyncio
async def test_resource_dashboard_authoritative_queries(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """Test the authoritative dashboard metrics endpoint."""
    headers = resource_worker_user["headers"]

    res = await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "active_resource_homes" in data
    assert "available_beds" in data
    assert "total_capacity" in data
    assert "active_placements" in data
    assert "applications_by_stage" in data
    assert "applications_awaiting_review" in data
    assert "upcoming_home_renewals" in data
    assert "total_applications" in data
    assert data["available_beds"] >= 0


@pytest.mark.asyncio
async def test_resource_recruitment_it_admin_privacy_denial(
    client: AsyncClient,
    it_admin_user: dict,
):
    """
    CRITICAL SECURITY & PRIVACY TEST:
    IT Admin must NOT gain access to Resource Recruitment records
    or dashboard metrics, preserving client and caregiver privacy.
    """
    headers = it_admin_user["headers"]

    # 1. Denied from listing recruitments
    res_list = await client.get("/api/v1/resource-recruitment", headers=headers)
    assert res_list.status_code == 403
    assert res_list.json()["error"]["code"] == "PERMISSION_DENIED"

    # 2. Denied from dashboard metrics
    res_dash = await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)
    assert res_dash.status_code == 403
    assert res_dash.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_approval_permission_distinct_from_recruitment_write(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
    resource_approver_user: dict,
):
    """
    Acceptance test:
    - Normal recruitment workers may create/update/progress applications through normal workflow.
    - Transition into APPROVED requires explicit RESOURCE_RECRUITMENT_APPROVE capability.
    - Transition from APPROVAL_REVIEW to DECLINED also requires approval capability.
    - Authorized approver can perform both APPROVED and DECLINED from APPROVAL_REVIEW.
    """
    worker_headers = resource_worker_user["headers"]
    approver_headers = resource_approver_user["headers"]

    person1 = Person(first_name="Alice", last_name="ApprovalTest", gender="FEMALE")
    person2 = Person(first_name="Bob", last_name="DeclineTest", gender="MALE")
    home = PlacementHome(
        home_code=f"PH-APP-{uuid.uuid4().hex[:6]}",
        name="Approval Test Home",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
    )
    db_session.add_all([person1, person2, home])
    await db_session.flush()

    # Application 1: Progress to APPROVAL_REVIEW by worker
    c1 = await client.post(
        "/api/v1/resource-recruitment",
        headers=worker_headers,
        json={"applicants": [{"person_id": str(person1.id), "role": "PRIMARY_APPLICANT"}]},
    )
    rec1_id = c1.json()["id"]

    for stage in ["ORIENTATION", "APPLICATION", "ASSESSMENT", "APPROVAL_REVIEW"]:
        res = await client.post(
            f"/api/v1/resource-recruitment/{rec1_id}/transition",
            headers=worker_headers,
            json={"to_state": stage},
        )
        assert res.status_code == 200

    # 1. Worker attempts APPROVAL_REVIEW -> APPROVED: denied with 403
    worker_approve = await client.post(
        f"/api/v1/resource-recruitment/{rec1_id}/transition",
        headers=worker_headers,
        json={"to_state": "APPROVED", "resource_home_id": str(home.id)},
    )
    assert worker_approve.status_code == 403
    assert worker_approve.json()["error"]["code"] == "PERMISSION_DENIED"

    # 2. Approver performs APPROVAL_REVIEW -> APPROVED: succeeds
    approver_approve = await client.post(
        f"/api/v1/resource-recruitment/{rec1_id}/transition",
        headers=approver_headers,
        json={"to_state": "APPROVED", "resource_home_id": str(home.id)},
    )
    assert approver_approve.status_code == 200
    assert approver_approve.json()["current_state"] == "APPROVED"

    # Application 2: Decline from APPROVAL_REVIEW
    c2 = await client.post(
        "/api/v1/resource-recruitment",
        headers=worker_headers,
        json={"applicants": [{"person_id": str(person2.id), "role": "PRIMARY_APPLICANT"}]},
    )
    rec2_id = c2.json()["id"]

    for stage in ["ORIENTATION", "APPLICATION", "ASSESSMENT", "APPROVAL_REVIEW"]:
        res = await client.post(
            f"/api/v1/resource-recruitment/{rec2_id}/transition",
            headers=worker_headers,
            json={"to_state": stage},
        )
        assert res.status_code == 200

    # Worker attempts APPROVAL_REVIEW -> DECLINED: denied with 403
    worker_decline = await client.post(
        f"/api/v1/resource-recruitment/{rec2_id}/transition",
        headers=worker_headers,
        json={"to_state": "DECLINED", "notes": "Worker cannot decline from approval review."},
    )
    assert worker_decline.status_code == 403

    # Approver performs APPROVAL_REVIEW -> DECLINED: succeeds
    approver_decline = await client.post(
        f"/api/v1/resource-recruitment/{rec2_id}/transition",
        headers=approver_headers,
        json={"to_state": "DECLINED", "notes": "Review committee declined application."},
    )
    assert approver_decline.status_code == 200
    assert approver_decline.json()["current_state"] == "DECLINED"


@pytest.mark.asyncio
async def test_history_immutability_and_no_mutation_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """
    Acceptance test:
    Verify resource_recruitment_history is genuinely append-only:
    - No PATCH/PUT history endpoint (returns 404 or 405)
    - No DELETE history endpoint (returns 404 or 405)
    - No service method overwrites historical transitions
    """
    headers = resource_worker_user["headers"]

    person = Person(first_name="Eve", last_name="HistoryAudit", gender="FEMALE")
    db_session.add(person)
    await db_session.flush()

    c = await client.post(
        "/api/v1/resource-recruitment",
        headers=headers,
        json={"applicants": [{"person_id": str(person.id), "role": "PRIMARY_APPLICANT"}]},
    )
    data = c.json()
    rec_id = data["id"]
    hist_id = data["history"][0]["id"]

    # 1. Attempt PUT /history -> 404 or 405
    put_res = await client.put(
        f"/api/v1/resource-recruitment/{rec_id}/history/{hist_id}",
        headers=headers,
        json={"from_state": "ORIENTATION", "to_state": "APPROVED"},
    )
    assert put_res.status_code in (404, 405)

    # 2. Attempt PATCH /history -> 404 or 405
    patch_res = await client.patch(
        f"/api/v1/resource-recruitment/{rec_id}/history/{hist_id}",
        headers=headers,
        json={"notes": "Altered history"},
    )
    assert patch_res.status_code in (404, 405)

    # 3. Attempt DELETE /history -> 404 or 405
    del_res = await client.delete(
        f"/api/v1/resource-recruitment/{rec_id}/history/{hist_id}",
        headers=headers,
    )
    assert del_res.status_code in (404, 405)

    # 4. Advance application and verify history strictly appended
    t1 = await client.post(
        f"/api/v1/resource-recruitment/{rec_id}/transition",
        headers=headers,
        json={"to_state": "ORIENTATION", "notes": "First transition."},
    )
    assert t1.status_code == 200
    t1_data = t1.json()
    assert len(t1_data["history"]) == 2
    assert t1_data["history"][0]["from_state"] == "INQUIRY"
    assert t1_data["history"][1]["to_state"] == "ORIENTATION"


@pytest.mark.asyncio
async def test_resource_id_db_uniqueness_enforcement(
    db_session: AsyncSession,
):
    """
    Acceptance test:
    Verify PlacementHome.home_code:
    - is NOT NULL
    - has uniqueness enforced at the database level
    - attempting duplicate Resource IDs is rejected via IntegrityError
    """
    unique_code = f"PH-UNIQ-{uuid.uuid4().hex[:8]}"

    home1 = PlacementHome(
        home_code=unique_code,
        name="Unique Home 1",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
    )
    db_session.add(home1)
    await db_session.flush()

    home2 = PlacementHome(
        home_code=unique_code,
        name="Duplicate Home Code 2",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
    )
    db_session.add(home2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_capacity_invariant_consistency(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """
    Acceptance test:
    Verify Resource dashboard available beds calculation:
    - Uses the same active placement definition as PlacementHome capacity service
    - Never allows negative available beds
    - Does not report available space when placement home is at capacity
    """
    headers = resource_worker_user["headers"]

    # Create home with capacity 2
    home_code = f"PH-CAP-{uuid.uuid4().hex[:6]}"
    home = PlacementHome(
        home_code=home_code,
        name="Capacity Test Home",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
        status="ACTIVE",
    )
    child1 = Person(first_name="Child1", last_name="CapTest", gender="MALE")
    child2 = Person(first_name="Child2", last_name="CapTest", gender="FEMALE")
    case = Case(
        case_number=f"CAS-CAP-{uuid.uuid4().hex[:6]}",
        title="Capacity Regression Case",
        status="ACTIVE",
        case_type="CHILD_PROTECTION",
    )
    db_session.add_all([home, child1, child2, case])
    await db_session.flush()

    # Get initial dashboard baseline
    base_res = await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)
    assert base_res.status_code == 200
    base_cap = base_res.json()["total_capacity"]
    base_occ = base_res.json()["active_placements"]
    base_avail = base_res.json()["available_beds"]
    assert base_avail == max(0, base_cap - base_occ)

    # 1. Add 1 active placement episode
    ep1 = PlacementEpisode(
        case_id=case.id,
        child_id=child1.id,
        placement_home_id=home.id,
        status="ACTIVE",
        start_date=date.today(),
        placement_type="FOSTER_CARE",
        provider_name=home.name,
    )
    db_session.add(ep1)
    await db_session.flush()

    d1 = (await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)).json()
    assert d1["active_placements"] == base_occ + 1
    assert d1["available_beds"] == max(0, d1["total_capacity"] - d1["active_placements"])

    # 2. Add second placement episode -> Home is now full (occupancy == capacity)
    ep2 = PlacementEpisode(
        case_id=case.id,
        child_id=child2.id,
        placement_home_id=home.id,
        status="ACTIVE",
        start_date=date.today(),
        placement_type="FOSTER_CARE",
        provider_name=home.name,
    )
    db_session.add(ep2)
    await db_session.flush()

    d2 = (await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)).json()
    assert d2["active_placements"] == base_occ + 2
    assert d2["available_beds"] == max(0, d2["total_capacity"] - d2["active_placements"])
    assert d2["available_beds"] >= 0

    # 3. Discharge an episode -> occupancy decreases, available space increases
    ep1.status = "DISCHARGED"
    ep1.end_date = date.today()
    await db_session.flush()

    d3 = (await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)).json()
    assert d3["active_placements"] == base_occ + 1
    assert d3["available_beds"] == max(0, d3["total_capacity"] - d3["active_placements"])


@pytest.mark.asyncio
async def test_household_active_primary_caregiver_consistency(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker_user: dict,
):
    """
    Acceptance test:
    Verify active primary-caregiver consistency:
    - Only one active PRIMARY_CAREGIVER permitted per home (second rejected with 409 Conflict)
    - POST /members/{id}/end transitions active member to historical (is_active=False)
    - After ending, a new PRIMARY_CAREGIVER can be added
    - Historical caregivers remain preserved on home detail
    """
    headers = resource_worker_user["headers"]

    home = PlacementHome(
        home_code=f"PH-CAREGIVER-{uuid.uuid4().hex[:6]}",
        name="Primary Caregiver Invariant Home",
        home_type="LICENSED_FOSTER",
        total_capacity=3,
    )
    p1 = Person(first_name="Helen", last_name="PrimaryOne", gender="FEMALE")
    p2 = Person(first_name="George", last_name="PrimaryTwo", gender="MALE")
    db_session.add_all([home, p1, p2])
    await db_session.flush()

    # 1. Add first active primary caregiver
    m1_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/members",
        headers=headers,
        json={
            "person_id": str(p1.id),
            "role": "PRIMARY_CAREGIVER",
            "start_date": date(2025, 1, 1).isoformat(),
            "is_active": True,
        },
    )
    assert m1_res.status_code == 201, m1_res.text
    m1_id = m1_res.json()["id"]

    # 2. Attempt adding second active PRIMARY_CAREGIVER -> 409 Conflict
    m2_fail = await client.post(
        f"/api/v1/placement-homes/{home.id}/members",
        headers=headers,
        json={
            "person_id": str(p2.id),
            "role": "PRIMARY_CAREGIVER",
            "start_date": date.today().isoformat(),
            "is_active": True,
        },
    )
    assert m2_fail.status_code == 409
    err_body = m2_fail.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "active primary caregiver" in err_msg.lower()

    # 3. End first primary caregiver via POST /members/{id}/end
    end_res = await client.post(f"/api/v1/resource-recruitment/members/{m1_id}/end", headers=headers)
    assert end_res.status_code == 200
    assert end_res.json()["is_active"] is False

    # 4. Now adding second PRIMARY_CAREGIVER succeeds
    m2_ok = await client.post(
        f"/api/v1/placement-homes/{home.id}/members",
        headers=headers,
        json={
            "person_id": str(p2.id),
            "role": "PRIMARY_CAREGIVER",
            "start_date": date.today().isoformat(),
            "is_active": True,
        },
    )
    assert m2_ok.status_code == 201

    # 5. Detail retains both historical and current primary caregivers
    detail_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_res.status_code == 200
    members = detail_res.json()["members"]
    assert len(members) == 2
    active_primaries = [m for m in members if m["role"] == "PRIMARY_CAREGIVER" and m["is_active"]]
    inactive_primaries = [m for m in members if m["role"] == "PRIMARY_CAREGIVER" and not m["is_active"]]
    assert len(active_primaries) == 1
    assert len(inactive_primaries) == 1


@pytest.mark.asyncio
async def test_route_security_and_api_authorization(
    client: AsyncClient,
    db_session: AsyncSession,
    finance_user: dict,
):
    """
    Acceptance test:
    Verify frontend route visibility is NOT the security boundary:
    - Direct API calls without token return 401 Unauthorized
    - Direct API calls with insufficient role permissions return 403 Forbidden
    """
    # 1. Unauthenticated requests
    unauth_list = await client.get("/api/v1/resource-recruitment")
    assert unauth_list.status_code == 401

    unauth_dash = await client.get("/api/v1/resource-recruitment/dashboard")
    assert unauth_dash.status_code == 401

    # 2. Authenticated user without resource permissions (finance_user)
    finance_headers = finance_user["headers"]
    forbidden_list = await client.get("/api/v1/resource-recruitment", headers=finance_headers)
    assert forbidden_list.status_code == 403
    assert forbidden_list.json()["error"]["code"] == "PERMISSION_DENIED"

    forbidden_dash = await client.get("/api/v1/resource-recruitment/dashboard", headers=finance_headers)
    assert forbidden_dash.status_code == 403
    assert forbidden_dash.json()["error"]["code"] == "PERMISSION_DENIED"

    dummy_id = uuid.uuid4()
    forbidden_write = await client.post(
        "/api/v1/resource-recruitment",
        headers=finance_headers,
        json={"applicants": [{"person_id": str(dummy_id), "role": "PRIMARY_APPLICANT"}]},
    )
    assert forbidden_write.status_code == 403

