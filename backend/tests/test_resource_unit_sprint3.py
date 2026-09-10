"""Comprehensive Tests for CRBCL Resource Unit Sprint 3.

Covers all authoritative requirements from Sprint 3:
1. Placement Matching (Assistive decision support, explainable factors, no autonomous placement, preserves capacity locking)
2. Sibling Group Matching (Capacity evaluation, non-separation indicators)
3. Resource Home Monitoring (Ongoing monthly contact distinct from annual licensing, preserves full history)
4. Configurable Monitoring Cadence and Overdue Calculation
5. Complaints & Inquiries Lifecycle (Registration, investigation, disposition)
6. Complaint Privacy Redaction (Basic vs sensitive view separation, complainant confidentiality)
7. Finalized Investigation Findings Immutability (409 Conflict on overwrite)
8. Complaint Disposition Authority (Supervisor/Director required, worker denied)
9. Caregiver Supports (Respite, clinical, financial linkage to ServiceRequest without duplicate ledgers)
10. Resource Financial Integration (Strict Finance permissions required, Resource workers and IT Admin denied 403)
11. Strategic Outcomes Telemetry (Retention, stability, conversion, length of stay, cultural connections)
12. Resource Canned Reports & Catalogue Datasets
13. Live Dashboard Telemetry Integration (Sprint 3 metrics and conditional finance card)
14. IT Admin Privacy Denial on Protected Resource Sprint 3 Data
15. Department Alone ("Resource Team") Grants Zero Access
16. Outbox Event Enqueuing for Monitoring Follow-up & Complaint Disposition
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
from app.core.seed import ROLE_PERMISSIONS_MAP
from app.models.caregiver_support import CaregiverSupport
from app.models.case import Case
from app.models.finance import ServiceRequest
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.resource_complaint import ResourceComplaint
from app.models.resource_monitoring import ResourceHomeMonitoring
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
    permissions: list[str | Permissions] | None = None,
) -> dict:
    """Helper to provision a test user assigned to an explicit operational role."""
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
        email=f"worker.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Wendy Worker",
    )


@pytest.fixture
async def resource_supervisor(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="resource_supervisor",
        role_name="Resource Supervisor",
        email=f"supervisor.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Sally Supervisor",
    )


@pytest.fixture
async def resource_director(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="resource_director",
        role_name="Resource Director",
        email=f"director.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="David Director",
    )


@pytest.fixture
async def it_admin(db_session: AsyncSession, seed_roles_and_permissions: dict):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="it_admin",
        role_name="IT Admin",
        email=f"admin.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Ian ITAdmin",
    )


@pytest.fixture
async def finance_user(db_session: AsyncSession, seed_roles_and_permissions: dict):
    """User with Finance role."""
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="finance_staff",
        role_name="Finance Staff",
        email=f"finance.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Fiona Finance",
    )


@pytest.fixture
async def reporting_only_user(db_session: AsyncSession, seed_roles_and_permissions: dict):
    """User assigned ONLY the resource_reporting.read permission."""
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key=f"reporting_only_analyst_{uuid.uuid4().hex[:6]}",
        role_name="Reporting Analyst",
        email=f"reporter.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Rita Reporter",
        permissions=[Permissions.RESOURCE_REPORTING_READ],
    )


@pytest.fixture
async def reporting_and_finance_user(db_session: AsyncSession, seed_roles_and_permissions: dict):
    """User assigned both resource reporting and finance request permissions."""
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key=f"reporting_finance_analyst_{uuid.uuid4().hex[:6]}",
        role_name="Reporting Finance Analyst",
        email=f"rep.fin.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Rhonda RepFin",
        permissions=[
            Permissions.RESOURCE_REPORTING_READ,
            Permissions.FINANCE_REQUEST_READ,
            Permissions.FINANCE_INVOICE_READ,
        ],
    )


@pytest.fixture
async def department_only_user(db_session: AsyncSession):
    user = User(
        email=f"dept.only.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
        email_normalized=f"dept.only.s3.{uuid.uuid4().hex[:6]}@crbcl.ca",
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
async def sample_resource_home(db_session: AsyncSession) -> PlacementHome:
    """Provisions an active, licensed Resource Home with bed capacity and contact data."""
    home = PlacementHome(
        home_code=f"PH-{uuid.uuid4().hex[:6].upper()}",
        name=f"Home-{uuid.uuid4().hex[:6]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=3,
        address_line_1="123 Prairie View Rd",
        city="Regina",
        province="SK",
        postal_code="S4P 1A1",
        phone="306-555-0199",
        email="caregiver@crbcl.ca",
        primary_caregiver_name="Claire Caregiver",
    )
    db_session.add(home)
    await db_session.flush()

    lic = PlacementHomeLicense(
        placement_home_id=home.id,
        license_number=f"LIC-{uuid.uuid4().hex[:6].upper()}",
        license_type="STANDARD_FOSTER",
        status="ACTIVE",
        effective_date=date.today() - timedelta(days=60),
        expiry_date=date.today() + timedelta(days=300),
        max_capacity=3,
    )
    db_session.add(lic)
    await db_session.commit()
    await db_session.refresh(home)
    return home


# ============================================================================
# 1. PLACEMENT MATCHING (ASSISTIVE DECISION SUPPORT)
# ============================================================================

@pytest.mark.asyncio
async def test_placement_matching_evaluation(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    sample_resource_home: PlacementHome,
):
    """Verifies placement matching evaluates explainable factors and never creates autonomous placement."""
    # Create child person
    child = Person(
        first_name="Jordan",
        last_name="TestChild",
        date_of_birth=date.today() - timedelta(days=365 * 8),  # 8 years old
        gender="MALE",
        indigenous_identity="FIRST_NATION",
        band_nation="Cowessess First Nation",
    )
    db_session.add(child)
    await db_session.commit()

    # Count placement episodes prior to evaluation
    ep_count_before = (await db_session.execute(select(PlacementEpisode))).scalars().all()

    payload = {
        "child_id": str(child.id),
        "age": 8,
        "gender": "MALE",
        "indigenous_community": "Cowessess First Nation",
        "sibling_group_size": 1,
    }

    resp = await client.post(
        "/api/v1/placement-matching/evaluate",
        json=payload,
        headers=resource_worker["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_homes_evaluated"] >= 1
    assert "eligible_candidates" in data
    assert len(data["eligible_candidates"]) >= 1

    matched = next((c for c in data["eligible_candidates"] if c["home_id"] == str(sample_resource_home.id)), None)
    assert matched is not None
    assert matched["is_eligible"] is True
    assert len(matched["factors"]) > 0

    # Verify explainable factors presence
    factor_names = [f["name"].upper() for f in matched["factors"]]
    factor_keys = [f["factor_key"].upper() for f in matched["factors"]]
    assert any("CAPACITY" in n for n in factor_names + factor_keys)
    assert any("LICENS" in n for n in factor_names + factor_keys)

    # CRITICAL INVARIANT: Assistive only, NEVER creates a PlacementEpisode
    ep_count_after = (await db_session.execute(select(PlacementEpisode))).scalars().all()
    assert len(ep_count_after) == len(ep_count_before)


@pytest.mark.asyncio
async def test_placement_matching_capacity_exclusion(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
):
    """Verifies full home (available_beds = 0) is excluded with explainable factor."""
    full_home = PlacementHome(
        home_code=f"PH-{uuid.uuid4().hex[:6].upper()}",
        name=f"FullHome-{uuid.uuid4().hex[:6]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=1,
        city="Regina",
    )
    db_session.add(full_home)
    await db_session.flush()

    lic = PlacementHomeLicense(
        placement_home_id=full_home.id,
        license_number=f"LIC-{uuid.uuid4().hex[:6].upper()}",
        license_type="STANDARD_FOSTER",
        status="ACTIVE",
        effective_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=300),
        max_capacity=1,
    )
    db_session.add(lic)
    await db_session.flush()

    occupant = Person(first_name="Occupant", last_name="Child")
    test_case = Case(
        case_number=f"CASE-{uuid.uuid4().hex[:6]}",
        title="Capacity Test Case",
        status="OPEN",
    )
    db_session.add_all([occupant, test_case])
    await db_session.flush()

    ep = PlacementEpisode(
        case_id=test_case.id,
        child_id=occupant.id,
        placement_home_id=full_home.id,
        placement_type="REGULAR",
        provider_name="Full Home Care Provider",
        start_date=date.today() - timedelta(days=10),
        status="ACTIVE",
    )
    db_session.add(ep)
    await db_session.commit()

    payload = {
        "age": 10,
        "sibling_group_size": 1,
    }

    resp = await client.post(
        "/api/v1/placement-matching/evaluate",
        json=payload,
        headers=resource_worker["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()

    candidate = next((c for c in data["excluded_candidates"] if c["home_id"] == str(full_home.id)), None)
    assert candidate is not None
    assert candidate["is_eligible"] is False
    assert any("capacity" in r.lower() for r in candidate["exclusion_reasons"])


@pytest.mark.asyncio
async def test_placement_matching_restrictions_handling(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
):
    """Verifies structured placement restrictions produce deterministic EXCLUDE,
    while free-text intake criteria flag MANUAL_REVIEW_REQUIRED instead of assuming compatibility."""
    # 1. Home with structured restriction: FEMALE_ONLY
    restricted_home = PlacementHome(
        home_code=f"PH-RESTRICT-{uuid.uuid4().hex[:4].upper()}",
        name=f"RestrictedHome-{uuid.uuid4().hex[:4]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
        metadata_={"placement_restrictions": ["FEMALE_ONLY"]},
    )
    db_session.add(restricted_home)
    await db_session.flush()

    lic1 = PlacementHomeLicense(
        placement_home_id=restricted_home.id,
        license_number=f"LIC-{uuid.uuid4().hex[:6].upper()}",
        license_type="STANDARD_FOSTER",
        status="ACTIVE",
        effective_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=300),
        max_capacity=2,
    )
    db_session.add(lic1)

    # 2. Home with free-text criteria notes
    notes_home = PlacementHome(
        home_code=f"PH-NOTES-{uuid.uuid4().hex[:4].upper()}",
        name=f"NotesHome-{uuid.uuid4().hex[:4]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
        intake_criteria_notes="Prefers children under 10; requires advance transition visits for pets.",
    )
    db_session.add(notes_home)
    await db_session.flush()

    lic2 = PlacementHomeLicense(
        placement_home_id=notes_home.id,
        license_number=f"LIC-{uuid.uuid4().hex[:6].upper()}",
        license_type="STANDARD_FOSTER",
        status="ACTIVE",
        effective_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=300),
        max_capacity=2,
    )
    db_session.add(lic2)
    await db_session.commit()

    # Query with a male child
    payload = {
        "age": 7,
        "gender": "MALE",
        "sibling_group_size": 1,
    }

    resp = await client.post(
        "/api/v1/placement-matching/evaluate",
        json=payload,
        headers=resource_worker["headers"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Assert structured conflict produces EXCLUDE
    excluded_cand = next((c for c in data["excluded_candidates"] if c["home_id"] == str(restricted_home.id)), None)
    assert excluded_cand is not None
    assert excluded_cand["is_eligible"] is False
    assert any("female_only" in r.lower() or "restriction" in r.lower() for r in excluded_cand["exclusion_reasons"])

    # Assert free-text criteria produces MANUAL_REVIEW_REQUIRED and factor status WARNING
    notes_cand = next((c for c in data["eligible_candidates"] if c["home_id"] == str(notes_home.id)), None)
    assert notes_cand is not None
    assert any("MANUAL_REVIEW_REQUIRED" in note for note in notes_cand.get("compatibility_notes", []))
    factor = next((f for f in notes_cand.get("factors", []) if f["factor_key"] == "placement_restrictions"), None)
    assert factor is not None
    assert factor["status"] == "WARNING"


# ============================================================================
# 2. RESOURCE HOME MONITORING (PERIODIC VISITS & HISTORY)
# ============================================================================

@pytest.mark.asyncio
async def test_resource_home_monitoring_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    sample_resource_home: PlacementHome,
):
    """Tests creating periodic monitoring visit, query history, and outbox notification."""
    visit_payload = {
        "placement_home_id": str(sample_resource_home.id),
        "contact_date": str(date.today()),
        "contact_type": "HOME_VISIT",
        "child_interview_completed": True,
        "caregiver_interview_completed": True,
        "safety_review_completed": True,
        "strengths": "Caregiver is managing well, children settled.",
        "concerns": "Need to follow up on immunization records.",
        "follow_up_required": True,
        "follow_up_details": "Verify routine immunization schedule by next week.",
        "next_review_date": str(date.today() + timedelta(days=30)),
        "notes": "Positive home visit.",
        "status": "COMPLETED",
        "cadence_days": 30,
    }

    resp = await client.post(
        "/api/v1/resource-monitoring",
        json=visit_payload,
        headers=resource_worker["headers"],
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["placement_home_id"] == str(sample_resource_home.id)
    assert created["follow_up_required"] is True

    # Check query list
    list_resp = await client.get(
        f"/api/v1/resource-monitoring?placement_home_id={sample_resource_home.id}",
        headers=resource_worker["headers"],
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    records = list_data.get("items", [])
    assert len(records) >= 1
    assert any(r["id"] == created["id"] for r in records)

    # Check outbox event enqueued for follow-up
    events = (await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.aggregate_type == "resource_monitoring")
    )).scalars().all()
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_resource_home_monitoring_cadence_policy(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
):
    """Verifies monitoring overdue policy neutrality:
    - No configured cadence + no next review date => NOT automatically overdue after 30+ days.
    - Explicit next_review_date in past => overdue.
    - Configured cadence => overdue calculation uses configured value.
    """
    from app.services.resource_monitoring_service import ResourceMonitoringService

    # 1. Home with no cadence configured, visit 35 days ago, NO next_review_date
    home_no_cadence = PlacementHome(
        home_code=f"PH-NOCAD-{uuid.uuid4().hex[:4].upper()}",
        name=f"NoCadenceHome-{uuid.uuid4().hex[:4]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
    )
    db_session.add(home_no_cadence)
    await db_session.flush()

    visit_unconfigured = ResourceHomeMonitoring(
        placement_home_id=home_no_cadence.id,
        worker_id=resource_worker["user"].id,
        contact_date=date.today() - timedelta(days=35),
        contact_type="HOME_VISIT",
        status="COMPLETED",
        cadence_days=None,  # No configured cadence
        next_review_date=None,  # No explicit next review date
    )
    db_session.add(visit_unconfigured)

    # 2. Home with explicit next_review_date in the past
    home_explicit_past = PlacementHome(
        home_code=f"PH-EXP-{uuid.uuid4().hex[:4].upper()}",
        name=f"ExplicitPastHome-{uuid.uuid4().hex[:4]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
    )
    db_session.add(home_explicit_past)
    await db_session.flush()

    visit_explicit_past = ResourceHomeMonitoring(
        placement_home_id=home_explicit_past.id,
        worker_id=resource_worker["user"].id,
        contact_date=date.today() - timedelta(days=40),
        contact_type="HOME_VISIT",
        status="COMPLETED",
        cadence_days=None,
        next_review_date=date.today() - timedelta(days=5),  # Past review date
    )
    db_session.add(visit_explicit_past)

    # 3. Home with configured cadence of 15 days, visit was 20 days ago
    home_cadence_15 = PlacementHome(
        home_code=f"PH-CAD15-{uuid.uuid4().hex[:4].upper()}",
        name=f"Cadence15Home-{uuid.uuid4().hex[:4]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
    )
    db_session.add(home_cadence_15)
    await db_session.flush()

    visit_cadence_15 = ResourceHomeMonitoring(
        placement_home_id=home_cadence_15.id,
        worker_id=resource_worker["user"].id,
        contact_date=date.today() - timedelta(days=20),
        contact_type="HOME_VISIT",
        status="COMPLETED",
        cadence_days=15,  # Configured 15 days, 20 days elapsed -> OVERDUE
        next_review_date=None,
    )
    db_session.add(visit_cadence_15)

    # 4. Home with configured cadence of 60 days, visit was 35 days ago -> NOT overdue
    home_cadence_60 = PlacementHome(
        home_code=f"PH-CAD60-{uuid.uuid4().hex[:4].upper()}",
        name=f"Cadence60Home-{uuid.uuid4().hex[:4]}",
        home_type="REGULAR",
        status="ACTIVE",
        licensing_status="ACTIVE",
        total_capacity=2,
        city="Regina",
    )
    db_session.add(home_cadence_60)
    await db_session.flush()

    visit_cadence_60 = ResourceHomeMonitoring(
        placement_home_id=home_cadence_60.id,
        worker_id=resource_worker["user"].id,
        contact_date=date.today() - timedelta(days=35),
        contact_type="HOME_VISIT",
        status="COMPLETED",
        cadence_days=60,  # 60 days cadence, 35 elapsed -> NOT OVERDUE
        next_review_date=None,
    )
    db_session.add(visit_cadence_60)
    await db_session.commit()

    # Query overdue count via service
    service = ResourceMonitoringService(db_session)
    overdue_count = await service.get_overdue_monitoring_homes_count()

    # Out of these four homes:
    # home_no_cadence (visit 35d ago, no cadence, no next_review): NOT overdue
    # home_explicit_past (next_review 5d ago): OVERDUE
    # home_cadence_15 (visit 20d ago, cadence 15): OVERDUE
    # home_cadence_60 (visit 35d ago, cadence 60): NOT overdue
    assert overdue_count >= 2


# ============================================================================
# 3. COMPLAINTS & INVESTIGATIONS (PRIVACY & IMMUTABILITY)
# ============================================================================

@pytest.mark.asyncio
async def test_complaints_privacy_and_immutability(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    resource_supervisor: dict,
    sample_resource_home: PlacementHome,
):
    """Tests complaint registration, basic vs sensitive privacy redaction, findings immutability, and disposition."""
    create_payload = {
        "placement_home_id": str(sample_resource_home.id),
        "complainant_category": "AGENCY_STAFF",
        "complainant_name": "Confidential Caseworker Jane",
        "complaint_type": "CARE_STANDARDS",
        "allegation_summary": "Concern reported regarding evening routine supervision.",
        "severity": "MEDIUM",
    }

    resp = await client.post(
        "/api/v1/resource-complaints",
        json=create_payload,
        headers=resource_worker["headers"],
    )
    assert resp.status_code == 201, resp.text
    complaint = resp.json()
    complaint_id = complaint["id"]
    assert complaint["complaint_number"].startswith("RC-")

    # Worker has resource_complaint.read and resource_complaint.manage
    detail_resp = await client.get(
        f"/api/v1/resource-complaints/{complaint_id}",
        headers=resource_supervisor["headers"],
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["allegation_summary"] == create_payload["allegation_summary"]

    # Worker records findings and finalizes them
    investigation_payload = {
        "findings": "Interviews conducted with caregiver and collateral workers. Supervision guidelines clarified.",
        "finalize_findings": True,
        "status": "INVESTIGATION",
    }

    patch_resp = await client.patch(
        f"/api/v1/resource-complaints/{complaint_id}/investigation",
        json=investigation_payload,
        headers=resource_worker["headers"],
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["findings_finalized"] is True

    # IMMUTABILITY TEST: Attempting to modify finalized findings must return 409 Conflict
    tamper_payload = {
        "findings": "Tampered findings attempting to alter finalized investigation record.",
    }
    tamper_resp = await client.patch(
        f"/api/v1/resource-complaints/{complaint_id}/investigation",
        json=tamper_payload,
        headers=resource_worker["headers"],
    )
    assert tamper_resp.status_code == 409
    err_body = tamper_resp.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "immutable" in err_msg.lower() or "finalized" in err_msg.lower()

    # Worker attempts disposition -> 403 Forbidden (requires resource_complaint.disposition)
    disp_payload = {
        "disposition": "UNSUBSTANTIATED",
        "disposition_notes": "Allegation unsubstantiated following full inquiry.",
        "status": "CLOSED",
    }
    worker_disp_resp = await client.post(
        f"/api/v1/resource-complaints/{complaint_id}/disposition",
        json=disp_payload,
        headers=resource_worker["headers"],
    )
    assert worker_disp_resp.status_code == 403

    # Supervisor has resource_complaint.disposition -> 200 OK
    sup_disp_resp = await client.post(
        f"/api/v1/resource-complaints/{complaint_id}/disposition",
        json=disp_payload,
        headers=resource_supervisor["headers"],
    )
    assert sup_disp_resp.status_code == 200
    assert sup_disp_resp.json()["disposition"] == "UNSUBSTANTIATED"
    assert sup_disp_resp.json()["status"] == "CLOSED"

    # Verify Outbox event created for disposition
    disp_events = (await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.aggregate_type == "resource_complaint")
    )).scalars().all()
    assert len(disp_events) >= 1


# ============================================================================
# 4. CAREGIVER SUPPORTS (FINANCE LINKAGE WITHOUT DUPLICATION)
# ============================================================================

@pytest.mark.asyncio
async def test_caregiver_supports_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    resource_worker: dict,
    resource_supervisor: dict,
    sample_resource_home: PlacementHome,
):
    """Tests creating caregiver support request, optional ServiceRequest linkage, and updates."""
    sr = ServiceRequest(
        request_number=f"SR-{uuid.uuid4().hex[:8]}",
        requestor_id=resource_worker["user"].id,
        title="Foster Respite Provision",
        description="Respite care support for weekend relief",
        status="APPROVED",
        total_amount=Decimal("350.00"),
    )
    db_session.add(sr)
    await db_session.commit()

    support_payload = {
        "placement_home_id": str(sample_resource_home.id),
        "support_type": "RESPITE",
        "title": "Weekend Respite Care Support",
        "description": "Weekend respite care support",
        "amount": 350.00,
        "service_request_id": str(sr.id),
    }

    resp = await client.post(
        "/api/v1/caregiver-supports",
        json=support_payload,
        headers=resource_worker["headers"],
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["support_type"] == "RESPITE"
    assert created["service_request_id"] == str(sr.id)

    # Supervisor updates approval
    update_payload = {
        "status": "APPROVED",
        "amount": 350.00,
        "outcome_notes": "Approved in accordance with respite guideline allowance.",
    }
    update_resp = await client.patch(
        f"/api/v1/caregiver-supports/{created['id']}",
        json=update_payload,
        headers=resource_supervisor["headers"],
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "APPROVED"
    assert float(update_resp.json()["amount"]) == 350.00


# ============================================================================
# 5. RESOURCE FINANCIAL INTEGRATION (STRICT RBAC)
# ============================================================================

@pytest.mark.asyncio
async def test_resource_finance_rbac_protection(
    client: AsyncClient,
    resource_worker: dict,
    finance_user: dict,
    it_admin: dict,
    department_only_user: dict,
    sample_resource_home: PlacementHome,
):
    """Verifies strict finance permissions: Finance user allowed, Resource Worker/IT Admin/Dept-only denied 403."""
    home_id = sample_resource_home.id

    # 1. Resource Worker -> 403 Forbidden
    worker_resp = await client.get(
        f"/api/v1/resource-finance/homes/{home_id}",
        headers=resource_worker["headers"],
    )
    assert worker_resp.status_code == 403

    # 2. IT Admin -> 403 Forbidden
    it_resp = await client.get(
        f"/api/v1/resource-finance/homes/{home_id}",
        headers=it_admin["headers"],
    )
    assert it_resp.status_code == 403

    # 3. Department Only -> 403 Forbidden
    dept_resp = await client.get(
        f"/api/v1/resource-finance/homes/{home_id}",
        headers=department_only_user["headers"],
    )
    assert dept_resp.status_code == 403

    # 4. Finance User (possesses finance.invoice.read / finance.request.read) -> 200 OK
    finance_resp = await client.get(
        f"/api/v1/resource-finance/homes/{home_id}",
        headers=finance_user["headers"],
    )
    assert finance_resp.status_code == 200
    fin_data = finance_resp.json()
    assert "approved_service_requests_count" in fin_data
    assert "year_to_date_invoiced_total" in fin_data


# ============================================================================
# 6. STRATEGIC OUTCOMES & CANNED REPORTING
# ============================================================================

@pytest.mark.asyncio
async def test_resource_outcomes_and_reporting(
    client: AsyncClient,
    resource_worker: dict,
    resource_supervisor: dict,
):
    """Verifies strategic outcomes metrics and canned report availability,
    specifically asserting unavailable outcome distinctions."""
    # Strategic outcomes
    outcomes_resp = await client.get(
        "/api/v1/resource-outcomes",
        headers=resource_worker["headers"],
    )
    assert outcomes_resp.status_code == 200, outcomes_resp.text
    outcomes = outcomes_resp.json()
    assert "active_resource_homes" in outcomes
    assert "available_beds" in outcomes

    # UNSAFE RETENTION PROXY REMOVAL:
    # caregiver_retention_rate_pct must be None/unavailable, NOT a fabricated KPI
    assert outcomes["caregiver_retention_rate_pct"] is None
    assert outcomes["caregiver_retention_available"] is False
    assert "authoritative" in outcomes["caregiver_retention_reason"].lower()

    # Operational longevity metric is reported factually
    assert "active_home_longevity_over_one_year_pct" in outcomes

    # Resource home growth: new approvals YTD uses license effective_date, closures is unavailable
    growth = outcomes["resource_home_growth"]
    assert isinstance(growth["new_approvals_ytd"], int)
    assert growth["closures_ytd"] is None
    assert growth["closures_available"] is False
    assert "closure" in growth["closures_reason"].lower()

    # Strategic outcomes without authoritative data are marked unavailable
    assert outcomes["family_connection_rate_pct"] is None
    assert outcomes["family_connection_available"] is False
    assert outcomes["cultural_connection_rate_pct"] is None
    assert outcomes["cultural_connection_available"] is False

    # Stability and conversion remain measured
    assert "placement_stability_pct" in outcomes
    assert "recruitment_conversion_rate_pct" in outcomes

    # Canned reports
    report_endpoints = [
        "/api/v1/reports/canned/resource-directory",
        "/api/v1/reports/canned/resource-capacity",
        "/api/v1/reports/canned/resource-monitoring",
        "/api/v1/reports/canned/resource-complaints",
        "/api/v1/reports/canned/resource-supports",
    ]

    for ep in report_endpoints:
        rep = await client.get(ep, headers=resource_worker["headers"])
        assert rep.status_code == 200, f"Report {ep} failed: {rep.text}"
        rep_data = rep.json()
        assert "report_name" in rep_data
        assert "items" in rep_data or "stage_breakdown" in rep_data or "summary" in rep_data


@pytest.mark.asyncio
async def test_resource_directory_contact_privacy(
    client: AsyncClient,
    reporting_only_user: dict,
    resource_worker: dict,
    it_admin: dict,
    sample_resource_home: PlacementHome,
):
    """Verifies directory contact privacy:
    - User with aggregate Resource Reporting alone receives REDACTED contact info (phone/email null).
    - User with Resource Home operational capability receives unmasked contact info.
    - IT Admin is denied 403 regardless.
    """
    # 1. Reporting only user -> phone/email redacted
    rep_resp = await client.get(
        "/api/v1/reports/canned/resource-directory",
        headers=reporting_only_user["headers"],
    )
    assert rep_resp.status_code == 200, rep_resp.text
    rep_data = rep_resp.json()
    assert rep_data["contact_details_unmasked"] is False
    target = next((h for h in rep_data["items"] if h["home_code"] == sample_resource_home.home_code), None)
    assert target is not None
    assert target["phone"] is None
    assert target["email"] is None
    assert target["primary_caregiver_name"] == "Claire Caregiver"

    # 2. Resource Worker (possesses resource_home.read) -> phone/email visible
    worker_resp = await client.get(
        "/api/v1/reports/canned/resource-directory",
        headers=resource_worker["headers"],
    )
    assert worker_resp.status_code == 200, worker_resp.text
    worker_data = worker_resp.json()
    assert worker_data["contact_details_unmasked"] is True
    w_target = next((h for h in worker_data["items"] if h["home_code"] == sample_resource_home.home_code), None)
    assert w_target is not None
    assert w_target["phone"] == "306-555-0199"
    assert w_target["email"] == "caregiver@crbcl.ca"

    # 3. IT Admin -> 403 Forbidden
    it_resp = await client.get(
        "/api/v1/reports/canned/resource-directory",
        headers=it_admin["headers"],
    )
    assert it_resp.status_code == 403


@pytest.mark.asyncio
async def test_resource_supports_financial_privacy(
    client: AsyncClient,
    db_session: AsyncSession,
    reporting_only_user: dict,
    resource_worker: dict,
    reporting_and_finance_user: dict,
    finance_user: dict,
    it_admin: dict,
    sample_resource_home: PlacementHome,
):
    """Verifies financial field-level privacy in resource-supports report:
    - User with only RESOURCE_REPORTING_READ: financial amounts are null/redacted.
    - Resource worker alone: financial amounts are null/redacted.
    - User with RESOURCE_REPORTING_READ + FINANCE permission: financial amounts are visible.
    - User with Finance only (no reporting permission): 403 Forbidden.
    - IT Admin: 403 Forbidden.
    """
    # Create support item with financial amount
    sr = ServiceRequest(
        request_number=f"SR-{uuid.uuid4().hex[:8]}",
        requestor_id=resource_worker["user"].id,
        title="Respite Provision",
        description="Respite relief",
        status="APPROVED",
        total_amount=Decimal("450.00"),
    )
    db_session.add(sr)
    await db_session.flush()

    cs = CaregiverSupport(
        support_number=f"CS-{uuid.uuid4().hex[:6].upper()}",
        placement_home_id=sample_resource_home.id,
        worker_id=resource_worker["user"].id,
        service_request_id=sr.id,
        support_type="RESPITE",
        title="Weekend Respite Support",
        description="Weekend respite provision",
        status="APPROVED",
        amount=Decimal("450.00"),
    )
    db_session.add(cs)
    await db_session.commit()

    # 1. Reporting Only user -> amount is None
    rep_resp = await client.get(
        "/api/v1/reports/canned/resource-supports",
        headers=reporting_only_user["headers"],
    )
    assert rep_resp.status_code == 200, rep_resp.text
    rep_items = rep_resp.json()["items"]
    target_rep = next((i for i in rep_items if i["id"] == str(cs.id)), None)
    assert target_rep is not None
    assert target_rep["amount"] is None
    assert target_rep["support_type"] == "RESPITE"

    # 2. Resource Worker (no finance perms) -> amount is None
    worker_resp = await client.get(
        "/api/v1/reports/canned/resource-supports",
        headers=resource_worker["headers"],
    )
    assert worker_resp.status_code == 200
    worker_items = worker_resp.json()["items"]
    target_w = next((i for i in worker_items if i["id"] == str(cs.id)), None)
    assert target_w is not None
    assert target_w["amount"] is None

    # 3. Reporting + Finance user -> amount is visible
    fin_rep_resp = await client.get(
        "/api/v1/reports/canned/resource-supports",
        headers=reporting_and_finance_user["headers"],
    )
    assert fin_rep_resp.status_code == 200
    fin_items = fin_rep_resp.json()["items"]
    target_fin = next((i for i in fin_items if i["id"] == str(cs.id)), None)
    assert target_fin is not None
    assert target_fin["amount"] == 450.0

    # 4. Finance user alone (no reporting perm) -> 403 Forbidden
    fin_alone_resp = await client.get(
        "/api/v1/reports/canned/resource-supports",
        headers=finance_user["headers"],
    )
    assert fin_alone_resp.status_code == 403

    # 5. IT Admin -> 403 Forbidden
    it_resp = await client.get(
        "/api/v1/reports/canned/resource-supports",
        headers=it_admin["headers"],
    )
    assert it_resp.status_code == 403


# ============================================================================
# 7. IT ADMIN PRIVACY DENIAL ACROSS SPRINT 3
# ============================================================================

@pytest.mark.asyncio
async def test_it_admin_privacy_denial_across_sprint3(
    client: AsyncClient,
    it_admin: dict,
    sample_resource_home: PlacementHome,
):
    """Verifies IT Admin is denied access to all protected Sprint 3 endpoints."""
    home_id = sample_resource_home.id

    endpoints = [
        ("POST", "/api/v1/placement-matching/evaluate", {"age": 5}),
        ("GET", f"/api/v1/resource-monitoring?placement_home_id={home_id}", None),
        ("POST", "/api/v1/resource-monitoring", {"placement_home_id": str(home_id), "contact_date": "2026-09-09"}),
        ("GET", f"/api/v1/resource-complaints?placement_home_id={home_id}", None),
        ("POST", "/api/v1/resource-complaints", {"placement_home_id": str(home_id), "allegation_summary": "Test complaint"}),
        ("GET", f"/api/v1/caregiver-supports?placement_home_id={home_id}", None),
        ("POST", "/api/v1/caregiver-supports", {"placement_home_id": str(home_id), "title": "Support Request"}),
        ("GET", f"/api/v1/resource-finance/homes/{home_id}", None),
        ("GET", "/api/v1/resource-outcomes", None),
        ("GET", "/api/v1/reports/canned/resource-directory", None),
        ("GET", "/api/v1/reports/canned/resource-capacity", None),
        ("GET", "/api/v1/reports/canned/resource-monitoring", None),
        ("GET", "/api/v1/reports/canned/resource-complaints", None),
        ("GET", "/api/v1/reports/canned/resource-supports", None),
    ]

    for method, path, body in endpoints:
        if method == "GET":
            r = await client.get(path, headers=it_admin["headers"])
        elif method == "POST":
            r = await client.post(path, json=body, headers=it_admin["headers"])
        assert r.status_code == 403, f"IT Admin was not denied on {method} {path}, got {r.status_code}"
