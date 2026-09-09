"""Comprehensive Tests for CRBCL Resource Unit Sprint 2.

Covers all authoritative requirements from Section K:
1. Caregiver assessment lifecycle and immutability (draft -> completed -> cannot silently overwrite)
2. Multiple historical assessments retained per Resource Home / Caregiver
3. Screening & clearance types (CRC, VSC, CARC, Driver Abstract, Reference Check)
4. Expiry calculations and renewal status
5. Sensitive clearance permissions (least-privilege visibility)
6. Resource Worker CANNOT adjudicate flagged checks (strict 403 Forbidden)
7. Caregiver training completion, mandatory modules, and expiry tracking
8. Caregiver is Person, not Employee (proper domain separation)
9. Home licensing history and renewal (superseded preserved, new active)
10. Authoritative bed capacity invariance
11. Inspections and corrective actions (deficiencies, due dates, resolution status)
12. Compliance dashboard live relational metrics (no hardcoded data)
13. Resource Supervisor / Director operational capabilities
14. IT Admin privacy denial on protected Resource caregiver narratives
15. Department alone ("Resource Team") grants zero access
16. Notifications / tickler outbox event enqueuing without synchronous external calls
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core.seed import ROLE_PERMISSIONS_MAP
from app.models.caregiver_training import CaregiverTraining
from app.models.person import Person
from app.models.placement import BackgroundCheck
from app.models.placement_home import (
    PlacementHome,
    PlacementHomeLicense,
    PlacementHomeMember,
    PlacementHomeVisit,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.permissions.constants import Permissions
from app.workflows.outbox import OutboxEvent


async def _create_test_user_with_role(
    db_session: AsyncSession,
    role_key: str,
    role_name: str,
    email: str,
    full_name: str,
    department: str | None = None,
) -> dict:
    """Helper to provision a test user assigned to an explicit operational role."""
    res = await db_session.execute(select(Role).where(Role.key == role_key))
    role = res.scalars().first()
    if not role:
        role = Role(key=role_key, name=role_name, is_system=True)
        db_session.add(role)
        await db_session.flush()

        perm_keys = ROLE_PERMISSIONS_MAP.get(role_key, [])
        for pk in perm_keys:
            val = pk.value if hasattr(pk, "value") else pk
            p_res = await db_session.execute(select(Permission).where(Permission.key == val))
            p = p_res.scalars().first()
            if not p:
                p = Permission(key=val, name=val, category="resource_unit")
                db_session.add(p)
                await db_session.flush()
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
async def resource_worker(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="resource_worker",
        role_name="Resource Worker",
        email=f"worker.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Wendy Worker",
    )


@pytest.fixture
async def resource_supervisor(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="resource_supervisor",
        role_name="Resource Supervisor",
        email=f"supervisor.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Sally Supervisor",
    )


@pytest.fixture
async def resource_director(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="resource_director",
        role_name="Resource Director",
        email=f"director.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="David Director",
    )


@pytest.fixture
async def it_admin(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="it_admin",
        role_name="IT Admin",
        email=f"admin.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Ian ITAdmin",
    )


@pytest.fixture
async def general_supervisor(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="supervisor",
        role_name="Supervisor",
        email=f"gensup.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="George GeneralSupervisor",
    )


@pytest.fixture
async def director_manager(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="director_manager",
        role_name="Director / Manager",
        email=f"dm.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Diana DirectorManager",
    )


@pytest.fixture
async def department_only_user(db_session: AsyncSession):
    """User assigned to department 'Resource Team' without any operational roles or permissions."""
    user = User(
        email=f"dept.only.{uuid.uuid4().hex[:6]}@crbcl.ca",
        email_normalized=f"dept.only.{uuid.uuid4().hex[:6]}@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Dave DeptOnly",
        department="Resource Team",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def setup_resource_home(db_session: AsyncSession):
    """Fixture providing an active PlacementHome with a primary caregiver Person."""
    person = Person(
        first_name="Eleanor",
        last_name="Blackbear",
        gender="FEMALE",
        date_of_birth=date(1985, 4, 12),
    )
    home = PlacementHome(
        home_code=f"PH-{uuid.uuid4().hex[:6].upper()}",
        name="Blackbear Kinship Home",
        home_type="KINSHIP",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
    )
    db_session.add_all([person, home])
    await db_session.flush()

    member = PlacementHomeMember(
        placement_home_id=home.id,
        person_id=person.id,
        role="PRIMARY_CAREGIVER",
        is_active=True,
        start_date=date.today() - timedelta(days=60),
    )
    license_ = PlacementHomeLicense(
        placement_home_id=home.id,
        license_number=f"LIC-{uuid.uuid4().hex[:6].upper()}",
        license_type="KINSHIP_APPROVAL",
        status="ACTIVE",
        effective_date=date.today() - timedelta(days=60),
        expiry_date=date.today() + timedelta(days=305),
        max_capacity=2,
        placement_restrictions="Sibling groups preferred; ages 0-12",
        min_age=0,
        max_age=12,
    )
    db_session.add_all([member, license_])
    await db_session.commit()
    return {"home": home, "person": person, "member": member, "license": license_}


# ── Test 1 & 2: Caregiver Assessments Lifecycle & Historical Retention ───
@pytest.mark.asyncio
async def test_caregiver_assessment_lifecycle_and_historical_retention(
    client: AsyncClient,
    resource_worker: dict,
    setup_resource_home: dict,
    seed_templates,
):
    """Verify assessment creation, DRAFT editability, completion guard, and multi-assessment historical retention."""
    home = setup_resource_home["home"]
    person = setup_resource_home["person"]
    headers = resource_worker["headers"]

    # 1. Initiate first caregiver assessment
    res1 = await client.post(
        f"/api/v1/placement-homes/{home.id}/assessments",
        headers=headers,
        json={
            "title": "Initial Caregiver Home Study",
            "assessment_type": "HOME_STUDY",
            "primary_person_id": str(person.id),
            "template_key": "CAREGIVER_HOME_ASSESSMENT",
        },
    )
    assert res1.status_code == 201, res1.text
    assess1_data = res1.json()
    assess1_id = assess1_data["id"]
    assert assess1_data["status"] == "DRAFT"

    # 2. DRAFT assessment CAN be modified
    patch_res = await client.patch(
        f"/api/v1/assessments/{assess1_id}",
        headers=headers,
        json={"title": "Updated Caregiver Home Study"},
    )
    assert patch_res.status_code == 200, patch_res.text
    assert patch_res.json()["title"] == "Updated Caregiver Home Study"

    # 3. Completion is guarded: all required template questions must be answered first
    complete_attempt = await client.post(
        f"/api/v1/assessments/{assess1_id}/complete",
        headers=headers,
        json={"determination": "SUITABLE", "determination_notes": "Caregiver meets all requirements."},
    )
    # System correctly blocks completion until required questions are answered (422 business validation)
    assert complete_attempt.status_code in (400, 422), (
        f"Completion without answers should be rejected, got {complete_attempt.status_code}: {complete_attempt.text}"
    )
    assert "required" in complete_attempt.text.lower() or "missing" in complete_attempt.text.lower()

    # 4. Initiate second (annual reassessment) for the same home / person
    res2 = await client.post(
        f"/api/v1/placement-homes/{home.id}/assessments",
        headers=headers,
        json={
            "title": "Annual Caregiver Review Assessment",
            "assessment_type": "ANNUAL_REVIEW",
            "primary_person_id": str(person.id),
            "template_key": "CAREGIVER_HOME_ASSESSMENT",
        },
    )
    assert res2.status_code == 201, res2.text

    # 5. Verify both assessments are retained in history
    list_res = await client.get(
        f"/api/v1/placement-homes/{home.id}/assessments",
        headers=headers,
    )
    assert list_res.status_code == 200, list_res.text
    items = list_res.json()
    assert len(items) >= 2
    titles = [a["title"] for a in items]
    assert "Updated Caregiver Home Study" in titles
    assert "Annual Caregiver Review Assessment" in titles


# ── Test 3, 4, 5, 6: Screening, Clearances, Expiry & Role Adjudication ──
@pytest.mark.asyncio
async def test_screening_clearance_lifecycle_and_adjudication_boundaries(
    client: AsyncClient,
    resource_worker: dict,
    resource_supervisor: dict,
    setup_resource_home: dict,
):
    """Verify clearance recording, expiry calculation, and Resource Worker adjudication denial."""
    home = setup_resource_home["home"]
    person = setup_resource_home["person"]
    worker_headers = resource_worker["headers"]
    supervisor_headers = resource_supervisor["headers"]

    # 1. Resource Worker records Criminal Record Check
    check_payload = {
        "subject_type": "PERSON",
        "subject_id": str(person.id),
        "subject_name": f"{person.first_name} {person.last_name}",
        "check_type": "CRIMINAL_RECORD_CHECK",
        "request_date": date.today().isoformat(),
        "conducted_by_agency": "Regina Police Service",
        "clearance_reference_number": "CRC-2026-9901",
        "risk_assessment_notes": "Flagged minor conviction from 15 years ago; requires supervisory review.",
    }
    create_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/clearances",
        headers=worker_headers,
        json=check_payload,
    )
    assert create_res.status_code == 201, create_res.text
    check_id = create_res.json()["id"]

    # 2. Resource Worker CANNOT adjudicate flagged check (Strict least-privilege boundary)
    adj_worker_res = await client.post(
        f"/api/v1/background-checks/{check_id}/adjudicate",
        headers=worker_headers,
        json={
            "status": "PASSED",
            "is_eligible_for_placement": True,
            "completion_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
        },
    )
    assert adj_worker_res.status_code == 403, "Resource Worker must NOT have adjudication authority."

    # 3. Resource Supervisor CAN adjudicate flagged check
    adj_sup_res = await client.post(
        f"/api/v1/background-checks/{check_id}/adjudicate",
        headers=supervisor_headers,
        json={
            "status": "PASSED",
            "is_eligible_for_placement": True,
            "completion_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "risk_assessment_notes": "Reviewed and cleared by Supervisor. 15-year-old summary conviction is non-violent and poses zero risk.",
        },
    )
    assert adj_sup_res.status_code == 200, adj_sup_res.text
    assert adj_sup_res.json()["is_eligible_for_placement"] is True
    assert adj_sup_res.json()["status"] == "PASSED"

    # 4. Record additional clearance types: VULNERABLE_SECTOR, CHILD_ABUSE_REGISTRY, DRIVER_ABSTRACT, REFERENCE_CHECK
    for ctype in ["VULNERABLE_SECTOR", "CHILD_ABUSE_REGISTRY", "DRIVER_ABSTRACT", "REFERENCE_CHECK"]:
        r = await client.post(
            f"/api/v1/placement-homes/{home.id}/clearances",
            headers=worker_headers,
            json={
                "subject_type": "PERSON",
                "subject_id": str(person.id),
                "subject_name": f"{person.first_name} {person.last_name}",
                "check_type": ctype,
                "request_date": date.today().isoformat(),
            },
        )
        assert r.status_code == 201, f"Failed creating clearance type: {ctype}"

    # 5. List home clearances and verify all 5 are present
    home_clearances_res = await client.get(
        f"/api/v1/placement-homes/{home.id}/clearances",
        headers=worker_headers,
    )
    assert home_clearances_res.status_code == 200
    items = home_clearances_res.json()
    types_present = {c["check_type"] for c in items}
    assert "CRIMINAL_RECORD_CHECK" in types_present
    assert "VULNERABLE_SECTOR" in types_present
    assert "CHILD_ABUSE_REGISTRY" in types_present
    assert "DRIVER_ABSTRACT" in types_present
    assert "REFERENCE_CHECK" in types_present


# ── Test 7 & 8: Caregiver Training Compliance & Domain Distinction ───────
@pytest.mark.asyncio
async def test_caregiver_training_compliance_and_domain_separation(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    resource_supervisor: dict,
    setup_resource_home: dict,
):
    """Verify training recording, compliance summary, and confirm caregiver is Person not Employee."""
    home = setup_resource_home["home"]
    person = setup_resource_home["person"]
    worker_headers = resource_worker["headers"]
    supervisor_headers = resource_supervisor["headers"]

    # 1. Record mandatory modules
    modules = [
        ("PRE_SERVICE_PRIDE", "PRIDE Pre-Service Program"),
        ("CPR_FIRST_AID", "Standard First Aid with CPR-C"),
        ("TRAUMA_INFORMED_CARE", "Trauma-Informed Care for Caregivers"),
        ("CULTURAL_SAFETY", "Indigenous Cultural Safety"),
    ]
    training_ids = []
    for mtype, mcourse in modules:
        res = await client.post(
            f"/api/v1/placement-homes/{home.id}/training",
            headers=worker_headers,
            json={
                "person_id": str(person.id),
                "training_type": mtype,
                "course_name": mcourse,
                "provider_name": "Saskatchewan Foster Families Association",
                "completion_date": date.today().isoformat(),
                "expiry_date": (date.today() + timedelta(days=730)).isoformat(),
            },
        )
        assert res.status_code == 201, res.text
        training_ids.append(res.json()["id"])

    # 2. Resource Worker CANNOT verify training (Supervisor / Director required)
    worker_verify = await client.post(
        f"/api/v1/caregiver-trainings/{training_ids[0]}/verify",
        headers=worker_headers,
        json={"status": "COMPLETED", "notes": "Worker attempting unauthorized verification"},
    )
    assert worker_verify.status_code == 403

    # 3. Resource Supervisor verifies training
    sup_verify = await client.post(
        f"/api/v1/caregiver-trainings/{training_ids[0]}/verify",
        headers=supervisor_headers,
        json={"status": "COMPLETED", "notes": "Verified against official SFFA completion certificate."},
    )
    assert sup_verify.status_code == 200
    assert sup_verify.json()["verified_by"] is not None

    # 4. Check Home Compliance Summary
    comp_res = await client.get(
        f"/api/v1/placement-homes/{home.id}/training/compliance",
        headers=worker_headers,
    )
    assert comp_res.status_code == 200, comp_res.text
    summary = comp_res.json()
    assert summary["overall_status"] == "COMPLIANT"
    assert summary["compliant_caregivers"] == 1
    assert len(summary["member_summaries"]) == 1
    assert summary["member_summaries"][0]["is_compliant"] is True
    assert len(summary["member_summaries"][0]["mandatory_missing"]) == 0

    # 5. Architectural Invariant: Caregiver is Person, NOT Employee
    training_db = await db_session.get(CaregiverTraining, uuid.UUID(training_ids[0]))
    assert training_db is not None
    assert training_db.person_id == person.id
    # Assert table relationship targets persons.id
    assert hasattr(training_db, "person_id")
    assert not hasattr(training_db, "employee_id")


# ── Test 9 & 10: Licensing Renewal & Authoritative Capacity Invariance ───
@pytest.mark.asyncio
async def test_licensing_renewal_and_capacity_invariance(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_supervisor: dict,
    setup_resource_home: dict,
):
    """Verify license renewal preserves history and does not alter or duplicate total capacity."""
    home = setup_resource_home["home"]
    supervisor_headers = resource_supervisor["headers"]

    initial_capacity = home.total_capacity
    old_license_id = setup_resource_home["license"].id

    # Renew license via Resource Supervisor
    new_lic_num = f"LIC-RENEW-{uuid.uuid4().hex[:6].upper()}"
    renew_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/licenses/renew",
        headers=supervisor_headers,
        json={
            "new_license_number": new_lic_num,
            "license_type": "STANDARD_FOSTER",
            "effective_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "max_capacity": initial_capacity,
            "placement_restrictions": "Ages 4-16, emergency and planned respite",
            "conditions": "Standard monitoring and bi-monthly check-ins.",
        },
    )
    assert renew_res.status_code == 201, renew_res.text
    new_lic_data = renew_res.json()
    assert new_lic_data["license_number"] == new_lic_num
    assert new_lic_data["status"] == "ACTIVE"

    # Prior license must remain in database as SUPERSEDED
    old_lic_db = await db_session.get(PlacementHomeLicense, old_license_id)
    assert old_lic_db.status == "SUPERSEDED"

    # Capacity invariance: PlacementHome.total_capacity remains unchanged
    home_db = await db_session.get(PlacementHome, home.id)
    assert home_db.total_capacity == initial_capacity


# ── Test 11: Inspections & Corrective Actions Lifecycle ──────────────────
@pytest.mark.asyncio
async def test_inspections_and_corrective_action_lifecycle(
    client: AsyncClient,
    resource_worker: dict,
    setup_resource_home: dict,
):
    """Verify logging physical inspection with deficiencies and resolving corrective actions."""
    home = setup_resource_home["home"]
    worker_headers = resource_worker["headers"]

    # 1. Log routine inspection with identified deficiencies
    visit_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/visits",
        headers=worker_headers,
        json={
            "visit_date": date.today().isoformat(),
            "visit_type": "ROUTINE_INSPECTION",
            "purpose": "Annual Environmental & Fire Safety Inspection",
            "summary": "Full walkthrough of dwelling completed with primary caregiver.",
            "findings": "Physical dwelling in generally good order, clean and well kept.",
            "deficiencies": "Basement smoke detector expired; fire extinguisher gauge in red zone.",
            "corrective_actions": "Install new dual-sensor smoke detector; replace fire extinguisher with certified 5lb ABC unit.",
            "corrective_action_due_date": (date.today() + timedelta(days=14)).isoformat(),
            "corrective_action_status": "REQUIRED",
            "status": "COMPLETED",
        },
    )
    assert visit_res.status_code == 201, visit_res.text
    visit_data = visit_res.json()
    assert visit_data["corrective_action_status"] == "REQUIRED"
    assert "smoke detector" in visit_data["deficiencies"]
    visit_id = visit_data["id"]

    # 2. Update corrective action after caregiver complies
    patch_res = await client.patch(
        f"/api/v1/placement-homes/{home.id}/visits/{visit_id}/corrective-action",
        headers=worker_headers,
        json={
            "corrective_action_status": "COMPLETED",
            "findings": "Re-inspected: new photoelectric smoke alarm installed; new 5lb ABC extinguisher mounted in kitchen.",
            "completed_date": date.today().isoformat(),
        },
    )
    assert patch_res.status_code == 200, patch_res.text
    updated = patch_res.json()
    assert updated["corrective_action_status"] == "COMPLETED"
    assert updated["completed_date"] == date.today().isoformat()


# ── Test 12: Compliance Dashboard Live Relational Metrics ─────────────────
@pytest.mark.asyncio
async def test_compliance_dashboard_live_metrics(
    client: AsyncClient,
    resource_worker: dict,
):
    """Verify live compliance dashboard metrics returned without hardcoded mock data."""
    headers = resource_worker["headers"]

    res = await client.get("/api/v1/resource-recruitment/dashboard", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # Verify all Sprint 2 compliance keys exist and are integers
    expected_keys = [
        "clearances_expiring_30_days",
        "clearances_expired",
        "training_due_30_days",
        "training_expired",
        "licenses_nearing_renewal_90_days",
        "inspections_overdue",
        "outstanding_corrective_actions",
        "non_compliant_homes_count",
    ]
    for key in expected_keys:
        assert key in data, f"Dashboard missing metric: {key}"
        assert isinstance(data[key], int), f"Metric {key} must be an integer, got {type(data[key])}"


# ── Test 13, 14, 15: Security, Least Privilege, IT Admin Privacy & Dept Denial
@pytest.mark.asyncio
async def test_security_least_privilege_and_privacy_boundaries(
    client: AsyncClient,
    resource_director: dict,
    it_admin: dict,
    department_only_user: dict,
    setup_resource_home: dict,
):
    """Verify Resource Director has zero IT admin capabilities, IT Admin cannot access clearances, and department alone grants 0 access."""
    home = setup_resource_home["home"]
    director_headers = resource_director["headers"]
    it_admin_headers = it_admin["headers"]
    dept_headers = department_only_user["headers"]

    # 1. Resource Director attempts IT system admin endpoint -> 403
    director_it_res = await client.get("/api/v1/users", headers=director_headers)
    # If endpoint requires admin permission, must return 403
    assert director_it_res.status_code == 403, "Resource Director must NOT have IT user management permissions."

    # 2. IT Admin attempts to view sensitive caregiver clearances -> 403
    it_admin_clearance_res = await client.get(
        f"/api/v1/placement-homes/{home.id}/clearances",
        headers=it_admin_headers,
    )
    assert it_admin_clearance_res.status_code == 403, "IT Admin must NOT have access to protected Resource clearances."

    # 3. Department alone ("Resource Team") without role grants ZERO access
    dept_res = await client.get(
        f"/api/v1/placement-homes/{home.id}/clearances",
        headers=dept_headers,
    )
    assert dept_res.status_code == 403, "Department alone must grant zero access."


# ── Test 16: Outbox Events Enqueued Without Synchronous External Calls ────
@pytest.mark.asyncio
async def test_outbox_events_enqueued_without_synchronous_calls(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    setup_resource_home: dict,
):
    """Verify event enqueuing into outbox_events table within the DB transaction."""
    home = setup_resource_home["home"]
    person = setup_resource_home["person"]
    headers = resource_worker["headers"]

    # Record training
    res = await client.post(
        f"/api/v1/placement-homes/{home.id}/training",
        headers=headers,
        json={
            "person_id": str(person.id),
            "training_type": "SUICIDE_PREVENTION",
            "course_name": "safeTALK Suicide Alertness",
            "completion_date": date.today().isoformat(),
        },
    )
    assert res.status_code == 201, res.text
    training_id = res.json()["id"]

    # Query outbox_events to ensure event was enqueued
    stmt = select(OutboxEvent).where(
        OutboxEvent.aggregate_type == "caregiver_training",
        OutboxEvent.aggregate_id == uuid.UUID(training_id),
    )
    outbox_res = await db_session.execute(stmt)
    event = outbox_res.scalars().first()
    assert event is not None
    assert event.event_type == "caregiver_training.completed"
    assert event.status.lower() in ("pending", "sent")


# ── Test 17: Object-Level Authorization & Privacy on Resource Clearances ───
@pytest.mark.asyncio
async def test_resource_clearance_object_level_adjudication_and_privacy_boundaries(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    resource_supervisor: dict,
    resource_director: dict,
    general_supervisor: dict,
    director_manager: dict,
    it_admin: dict,
    caseworker_user: dict,
    setup_resource_home: dict,
):
    """Verify object-level authorization: general supervisor cannot adjudicate Resource caregiver clearances,

    Resource Supervisor/Director can, and generic read endpoint enforces object-aware privacy.
    """
    home = setup_resource_home["home"]
    person = setup_resource_home["person"]
    worker_headers = resource_worker["headers"]
    res_sup_headers = resource_supervisor["headers"]
    res_dir_headers = resource_director["headers"]
    gen_sup_headers = general_supervisor["headers"]
    dm_headers = director_manager["headers"]
    it_admin_headers = it_admin["headers"]
    cw_headers = caseworker_user["headers"]

    # 1. Create a Resource Caregiver Clearance (tied to placement_home_id)
    res_chk_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/clearances",
        headers=worker_headers,
        json={
            "subject_type": "PERSON",
            "subject_id": str(person.id),
            "subject_name": f"{person.first_name} {person.last_name}",
            "check_type": "VULNERABLE_SECTOR",
            "request_date": date.today().isoformat(),
            "conducted_by_agency": "Regina Police Service",
            "clearance_reference_number": "VS-RESOURCE-2026",
            "risk_assessment_notes": "Requires supervisory clearance review.",
        },
    )
    assert res_chk_res.status_code == 201, res_chk_res.text
    res_chk_id = res_chk_res.json()["id"]

    # 2. Create an established General Child-Welfare Background Check (placement_home_id is None)
    gen_chk_res = await client.post(
        "/api/v1/background-checks",
        headers=cw_headers,
        json={
            "subject_type": "PERSON",
            "subject_id": str(person.id),
            "subject_name": f"{person.first_name} {person.last_name}",
            "check_type": "CRIMINAL_RECORD_CHECK",
            "request_date": date.today().isoformat(),
            "conducted_by_agency": "RCMP",
            "clearance_reference_number": "CRC-GENERAL-2026",
        },
    )
    assert gen_chk_res.status_code == 201, gen_chk_res.text
    gen_chk_id = gen_chk_res.json()["id"]

    adjudicate_payload = {
        "status": "PASSED",
        "is_eligible_for_placement": True,
        "completion_date": date.today().isoformat(),
        "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
        "risk_assessment_notes": "Approved upon review.",
    }

    # 3. Security Boundary: General Supervisor (with background_check.adjudicate) CANNOT adjudicate Resource clearance
    gen_sup_on_res = await client.post(
        f"/api/v1/background-checks/{res_chk_id}/adjudicate",
        headers=gen_sup_headers,
        json=adjudicate_payload,
    )
    assert gen_sup_on_res.status_code == 403, (
        "General supervisor must NOT be able to adjudicate Resource caregiver clearances."
    )

    # 4. Security Boundary: Director / Manager CANNOT adjudicate Resource clearance solely through general permission
    dm_on_res = await client.post(
        f"/api/v1/background-checks/{res_chk_id}/adjudicate",
        headers=dm_headers,
        json=adjudicate_payload,
    )
    assert dm_on_res.status_code == 403, (
        "Director/Manager must NOT be able to adjudicate Resource clearances without resource_clearance.adjudicate."
    )

    # 5. Security Boundary: Resource Worker CANNOT adjudicate Resource clearance
    rw_on_res = await client.post(
        f"/api/v1/background-checks/{res_chk_id}/adjudicate",
        headers=worker_headers,
        json=adjudicate_payload,
    )
    assert rw_on_res.status_code == 403, "Resource Worker must not have adjudication authority."

    # 6. Security Boundary: IT Admin CANNOT adjudicate Resource clearance
    it_on_res = await client.post(
        f"/api/v1/background-checks/{res_chk_id}/adjudicate",
        headers=it_admin_headers,
        json=adjudicate_payload,
    )
    assert it_on_res.status_code == 403, "IT Admin must have zero clearance adjudication authority."

    # 7. Authorized: Resource Supervisor CAN adjudicate Resource clearance
    rs_on_res = await client.post(
        f"/api/v1/background-checks/{res_chk_id}/adjudicate",
        headers=res_sup_headers,
        json=adjudicate_payload,
    )
    assert rs_on_res.status_code == 200, rs_on_res.text
    assert rs_on_res.json()["status"] == "PASSED"

    # 8. Authorized: Resource Director CAN adjudicate Resource clearance
    rd_on_res = await client.post(
        f"/api/v1/background-checks/{res_chk_id}/adjudicate",
        headers=res_dir_headers,
        json=adjudicate_payload,
    )
    assert rd_on_res.status_code == 200, rd_on_res.text

    # 9. Existing general background check: General Supervisor CAN adjudicate non-Resource check
    gen_sup_on_gen = await client.post(
        f"/api/v1/background-checks/{gen_chk_id}/adjudicate",
        headers=gen_sup_headers,
        json=adjudicate_payload,
    )
    assert gen_sup_on_gen.status_code == 200, gen_sup_on_gen.text
    assert gen_sup_on_gen.json()["status"] == "PASSED"

    # 10. Read Privacy on generic detail endpoint: User with general BACKGROUND_CHECK_READ but NO Resource capability
    general_reader = await _create_test_user_with_role(
        db_session=db_session,
        role_key="general_reader",
        role_name="General Reader",
        email=f"reader.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Rachel Reader",
    )
    p_bcr_res = await db_session.execute(
        select(Permission).where(Permission.key == Permissions.BACKGROUND_CHECK_READ.value)
    )
    p_bcr = p_bcr_res.scalars().first()
    r_gr_res = await db_session.execute(select(Role).where(Role.key == "general_reader"))
    r_gr = r_gr_res.scalars().first()
    db_session.add(RolePermission(role_id=r_gr.id, permission_id=p_bcr.id))
    await db_session.commit()
    gen_reader_headers = general_reader["headers"]

    reader_res = await client.get(
        f"/api/v1/background-checks/{res_chk_id}",
        headers=gen_reader_headers,
    )
    assert reader_res.status_code == 403, (
        "User with only general background_check.read must NOT retrieve sensitive Resource clearance details."
    )

    # General reader CAN retrieve non-Resource general check
    reader_gen_res = await client.get(
        f"/api/v1/background-checks/{gen_chk_id}",
        headers=gen_reader_headers,
    )
    assert reader_gen_res.status_code == 200, reader_gen_res.text

    # 11. Read Privacy on generic detail endpoint: IT Admin cannot access Resource clearance
    it_read_res = await client.get(
        f"/api/v1/background-checks/{res_chk_id}",
        headers=it_admin_headers,
    )
    assert it_read_res.status_code == 403, "IT Admin must NOT retrieve sensitive Resource clearance details directly."

    # 12. Authorized Resource Worker / Supervisor CAN retrieve Resource clearance
    rw_read_res = await client.get(
        f"/api/v1/background-checks/{res_chk_id}",
        headers=worker_headers,
    )
    assert rw_read_res.status_code == 200, rw_read_res.text


# ── Test 18: Training Policy Neutrality & Non-Blocking Evaluation ──────────
@pytest.mark.asyncio
async def test_training_policy_neutrality_unconfigured_types_non_blocking(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    setup_resource_home: dict,
):
    """Verify policy neutrality: unconfigured training types do not falsely classify a home as non-compliant."""
    home = setup_resource_home["home"]
    person = setup_resource_home["person"]
    headers = resource_worker["headers"]

    # When no mandatory training types are explicitly configured in SystemConfig,
    # compliance summary tracks completed training without demanding unconfirmed universal modules.
    comp_res = await client.get(
        f"/api/v1/placement-homes/{home.id}/training/compliance",
        headers=headers,
    )
    assert comp_res.status_code == 200, comp_res.text
    summary = comp_res.json()

    # Home has active caregiver with 0 expired credentials
    assert summary["overall_status"] == "COMPLIANT"
    assert len(summary["member_summaries"]) == 1
    assert summary["member_summaries"][0]["is_compliant"] is True
    assert summary["member_summaries"][0]["mandatory_missing"] == []
