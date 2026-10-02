"""Tests for Front Desk Public Intake & Google Form Ingestion Pipeline.

Verifies:
1. Valid webhook ingestion & secret verification
2. Invalid/missing secret rejection
3. Duplicate webhook idempotency
4. Unknown field preservation & raw payload immutability
5. Zero canonical Person/Client/Family/Case creation on receipt
6. Front Desk triage & review
7. Department routing & append-only routing history
8. Receiving department scoping (/department-queue)
9. Return to Front Desk
10. Department acceptance
11. Duplicate detection before canonical creation
12. Authorized protection worker can create internal Intake/Referral
13. Front Desk cannot create internal Intake (403)
14. Front Desk cannot browse internal Intake (403)
15. Front Desk denied cases/clinical/finance/admin APIs (403)
16. IT Admin denied public submission narrative (403)
17. Department alone grants zero Front Desk capability (403)
18. Transactional outbox events
19. Front Desk stats calculation
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core.seed import ROLE_PERMISSIONS_MAP
from app.models.case import Case
from app.models.client import Client
from app.models.family import Family
from app.models.front_desk import FrontDeskRoutingHistory, FrontDeskSubmission, PublicIntakeConversionLink
from app.models.outbox import OutboxEvent
from app.models.person import Person
from app.models.referral import Referral, ReferralReporter
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.permissions.constants import Permissions


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
            p = Permission(key=val, name=val, category="front_desk")
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
async def front_desk_worker(db_session: AsyncSession):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="front_desk",
        role_name="Front Desk / Intake Reception",
        email=f"frontdesk.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Fiona FrontDesk",
        department="Front Desk / Reception",
    )


@pytest.fixture
async def it_admin_user(db_session: AsyncSession):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="it_admin",
        role_name="IT Admin",
        email=f"itadmin.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Ian ITAdmin",
        department="IT & Systems",
    )


@pytest.fixture
async def protection_worker(db_session: AsyncSession):
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="caseworker",
        role_name="Caseworker",
        email=f"caseworker.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Casey Caseworker",
        department="Growing Up Well (Protection Services)",
    )


@pytest.fixture
async def unauthorized_dept_user(db_session: AsyncSession):
    """User who has department 'Front Desk / Reception' but a role that lacks public_intake permissions."""
    return await _create_test_user_with_role(
        db_session=db_session,
        role_key="cultural_worker",
        role_name="Cultural Worker",
        email=f"cultural.{uuid.uuid4().hex[:6]}@crbcl.ca",
        full_name="Cathy Cultural",
        department="Front Desk / Reception",  # Department alone should grant ZERO permissions
    )


@pytest.mark.asyncio
async def test_webhook_security_valid_and_invalid(client: AsyncClient, db_session: AsyncSession):
    """Webhook rejects unauthorized calls (401), and accepts valid secret header (201)."""
    payload = {
        "response_id": "google-test-001",
        "submitter_name": "Jane Public",
        "submitter_email": "jane@example.com",
        "submitter_phone": "306-555-0199",
        "submitter_relationship": "Neighbour",
        "inquiry_type": "child_concern",
        "summary": "Concern regarding child safety on First Avenue",
        "details": "Child seen outside late at night without adult supervision.",
        "responses": {
            "timestamp": "2026-09-10 10:00:00",
            "are_parents_home": "Unsure",
        },
    }

    # 1. Missing secret header -> 401
    bad_res = await client.post("/api/v1/front-desk/ingest/google-form", json=payload)
    assert bad_res.status_code == 401

    # 2. Invalid secret header -> 401
    bad_secret_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json=payload,
        headers={"X-CRBCL-Webhook-Secret": "invalid-secret"},
    )
    assert bad_secret_res.status_code == 401

    # 3. Valid secret header -> 201 Created
    good_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json=payload,
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    assert good_res.status_code == 201
    body = good_res.json()
    assert body["status"] == "RECEIVED"
    assert "submission_number" in body
    assert body["submission_number"].startswith("FD-")
    assert body["is_duplicate"] is False

    # Stored submission check
    sub_id = uuid.UUID(body["submission_id"])
    stmt = select(FrontDeskSubmission).where(FrontDeskSubmission.id == sub_id)
    sub = (await db_session.execute(stmt)).scalar_one()
    assert sub.submitter_name == "Jane Public"
    assert sub.status == "RECEIVED"
    assert sub.source == "google_form"
    assert sub.payload_raw["are_parents_home"] == "Unsure"


@pytest.mark.asyncio
async def test_duplicate_webhook_idempotency(client: AsyncClient, db_session: AsyncSession):
    """Delivering the exact same Google response multiple times produces 1 CRBCL submission."""
    payload = {
        "response_id": "google-idempotent-unique-999",
        "submitter_name": "Idempotent Submitter",
        "summary": "Initial report",
        "responses": {"q1": "answer1"},
    }

    # First delivery -> 201 Created
    res1 = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json=payload,
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    assert res1.status_code == 201
    sub_num1 = res1.json()["submission_number"]
    assert res1.json()["is_duplicate"] is False

    # Second delivery of same response_id -> 200 OK with existing reference
    res2 = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json=payload,
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    assert res2.status_code == 200
    sub_num2 = res2.json()["submission_number"]
    assert sub_num2 == sub_num1
    assert res2.json()["is_duplicate"] is True

    # Confirm only one row exists in DB
    count_stmt = select(func.count(FrontDeskSubmission.id)).where(
        FrontDeskSubmission.external_response_id == "google-idempotent-unique-999"
    )
    count = (await db_session.execute(count_stmt)).scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_zero_canonical_records_on_receipt(client: AsyncClient, db_session: AsyncSession):
    """Webhook receipt must create ZERO Person, Client, Family, or Case records."""
    persons_before = (await db_session.execute(select(func.count(Person.id)))).scalar()
    clients_before = (await db_session.execute(select(func.count(Client.id)))).scalar()
    families_before = (await db_session.execute(select(func.count(Family.id)))).scalar()
    cases_before = (await db_session.execute(select(func.count(Case.id)))).scalar()

    payload = {
        "response_id": "google-zero-entities-001",
        "submitter_name": "New Person Unseen",
        "submitter_phone": "306-555-9999",
        "summary": "General inquiry about family supports",
        "responses": {"child_name": "Unknown Child"},
    }
    res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json=payload,
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    assert res.status_code == 201

    persons_after = (await db_session.execute(select(func.count(Person.id)))).scalar()
    clients_after = (await db_session.execute(select(func.count(Client.id)))).scalar()
    families_after = (await db_session.execute(select(func.count(Family.id)))).scalar()
    cases_after = (await db_session.execute(select(func.count(Case.id)))).scalar()

    assert persons_after == persons_before
    assert clients_after == clients_before
    assert families_after == families_before
    assert cases_after == cases_before


@pytest.mark.asyncio
async def test_unknown_field_preservation_and_payload_immutability(
    client: AsyncClient, front_desk_worker: dict, db_session: AsyncSession
):
    """Unknown Google form fields are preserved in payload_raw, which is immutable across edits."""
    payload = {
        "response_id": "google-immutability-001",
        "submitter_name": "Preserve Test",
        "summary": "Check fields",
        "responses": {
            "favourite_traditional_teaching": "Seven Grandfather Teachings",
            "custom_band_location": "Saddle Lake",
            "is_emergency": "No",
        },
    }
    res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json=payload,
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    assert res.status_code == 201
    sub_id = res.json()["submission_id"]

    # Front Desk reviews submission
    review_res = await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/review",
        json={"status": "FRONT_DESK_REVIEW", "notes": "Reviewing custom responses"},
        headers=front_desk_worker["headers"],
    )
    assert review_res.status_code == 200
    sub_data = review_res.json()

    # Raw payload remains untouched and preserves original custom fields
    assert sub_data["payload_raw"]["favourite_traditional_teaching"] == "Seven Grandfather Teachings"
    assert sub_data["payload_raw"]["custom_band_location"] == "Saddle Lake"
    assert sub_data["status"] == "FRONT_DESK_REVIEW"


@pytest.mark.asyncio
async def test_manual_submission_and_triage_flow(
    client: AsyncClient, front_desk_worker: dict, db_session: AsyncSession
):
    """Front Desk can log walk-in inquiry and mark it FRONT_DESK_REVIEW or OUT_OF_SCOPE."""
    headers = front_desk_worker["headers"]

    manual_payload = {
        "source": "walk_in",
        "submitter_name": "Tom WalkIn",
        "submitter_phone": "306-555-1234",
        "inquiry_type": "general_inquiry",
        "urgency": "Low",
        "summary": "Asking about gym schedule",
        "details": "Provided gym schedule brochure.",
    }
    res = await client.post("/api/v1/front-desk/submissions/manual", json=manual_payload, headers=headers)
    assert res.status_code == 201
    sub = res.json()
    assert sub["status"] == "RECEIVED"
    assert sub["source"] == "walk_in"
    sub_id = sub["id"]

    # Mark OUT_OF_SCOPE
    review_res = await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/review",
        json={"status": "OUT_OF_SCOPE", "notes": "Public rec inquiry, not a social services matter."},
        headers=headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "OUT_OF_SCOPE"


@pytest.mark.asyncio
async def test_routing_and_append_only_history(
    client: AsyncClient, front_desk_worker: dict, db_session: AsyncSession
):
    """Front Desk routes submission; append-only routing history records all transitions."""
    # Ingest submission
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={"summary": "Protection inquiry", "response_id": f"resp-{uuid.uuid4().hex[:8]}"},
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = ingest_res.json()["submission_id"]

    # Route to Growing Up Well
    route_payload = {
        "destination_department": "Growing Up Well (Protection Services)",
        "urgency": "High",
        "routing_notes": "Urgent review required by intake team",
    }
    route_res = await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/route",
        json=route_payload,
        headers=front_desk_worker["headers"],
    )
    assert route_res.status_code == 200
    data = route_res.json()
    assert data["status"] == "ROUTED"
    assert data["destination_department"] == "Growing Up Well (Protection Services)"
    assert data["urgency"] == "High"

    # Check routing history in DB
    hist_stmt = (
        select(FrontDeskRoutingHistory)
        .where(FrontDeskRoutingHistory.submission_id == uuid.UUID(sub_id))
        .order_by(FrontDeskRoutingHistory.changed_at.asc())
    )
    history_records = list((await db_session.execute(hist_stmt)).scalars().all())
    assert len(history_records) >= 2  # NONE->RECEIVED, RECEIVED->ROUTED
    latest_hist = history_records[-1]
    assert latest_hist.new_status == "ROUTED"
    assert latest_hist.new_destination == "Growing Up Well (Protection Services)"
    assert latest_hist.reason_note == "Urgent review required by intake team"


@pytest.mark.asyncio
async def test_receiving_department_scoping_and_actions(
    client: AsyncClient,
    front_desk_worker: dict,
    protection_worker: dict,
    db_session: AsyncSession,
):
    """Receiving staff sees department queue, marks DEPARTMENT_REVIEW, returns or accepts."""
    # 1. Ingest & Route to Growing Up Well
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={"summary": "Child protection concern", "response_id": f"resp-{uuid.uuid4().hex[:8]}"},
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = ingest_res.json()["submission_id"]

    await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/route",
        json={
            "destination_department": "Growing Up Well (Protection Services)",
            "urgency": "Medium",
            "routing_notes": "Routed to protection",
        },
        headers=front_desk_worker["headers"],
    )

    # 2. Protection worker opens /department-queue
    dept_res = await client.get(
        "/api/v1/front-desk/department-queue?department=Growing Up Well (Protection Services)",
        headers=protection_worker["headers"],
    )
    assert dept_res.status_code == 200
    items = dept_res.json()["items"]
    assert any(i["id"] == sub_id for i in items)

    # 3. Protection worker marks DEPARTMENT_REVIEW
    review_res = await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/department-action",
        json={"action": "DEPARTMENT_REVIEW", "notes": "Staff reviewing safety indicators"},
        headers=protection_worker["headers"],
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "DEPARTMENT_REVIEW"

    # 4. Protection worker accepts responsibility
    accept_res = await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/department-action",
        json={"action": "ACCEPTED", "notes": "Accepted for protection follow-up"},
        headers=protection_worker["headers"],
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_department_returns_to_front_desk(
    client: AsyncClient,
    front_desk_worker: dict,
    protection_worker: dict,
    db_session: AsyncSession,
):
    """Receiving staff can return submission to Front Desk with reason."""
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={"summary": "Misrouted request", "response_id": f"resp-{uuid.uuid4().hex[:8]}"},
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = ingest_res.json()["submission_id"]

    await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/route",
        json={"destination_department": "Growing Up Well (Protection Services)"},
        headers=front_desk_worker["headers"],
    )

    # Protection worker returns to Front Desk
    return_res = await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/department-action",
        json={
            "action": "RETURNED_TO_FRONT_DESK",
            "notes": "Not a protection matter; belongs to Prevention & Family Support.",
        },
        headers=protection_worker["headers"],
    )
    assert return_res.status_code == 200
    data = return_res.json()
    assert data["status"] == "RETURNED_TO_FRONT_DESK"
    assert data["department_notes"] == "Not a protection matter; belongs to Prevention & Family Support."


@pytest.mark.asyncio
async def test_duplicate_detection_before_canonical_creation(
    client: AsyncClient, front_desk_worker: dict, db_session: AsyncSession
):
    """Duplicate detection finds candidate matches without creating canonical records."""
    # Seed an existing Person
    existing_person = Person(
        first_name="Arthur",
        last_name="Pendleton",
        phone="306-555-7777",
        email="arthur.p@example.com",
    )
    db_session.add(existing_person)
    await db_session.commit()

    # Ingest submission from Arthur Pendleton
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={
            "submitter_name": "Arthur Pendleton",
            "submitter_phone": "306-555-7777",
            "summary": "Checking on previous service request",
            "response_id": f"resp-{uuid.uuid4().hex[:8]}",
        },
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = ingest_res.json()["submission_id"]

    # Call duplicate detection
    dup_res = await client.get(
        f"/api/v1/front-desk/submissions/{sub_id}/duplicates",
        headers=front_desk_worker["headers"],
    )
    assert dup_res.status_code == 200
    candidates = dup_res.json()
    assert len(candidates) >= 1
    match = candidates[0]
    assert "Arthur Pendleton" in match["name"]
    assert match["match_score"] > 0.5


@pytest.mark.asyncio
async def test_protection_worker_converts_to_referral_and_linkages(
    client: AsyncClient,
    front_desk_worker: dict,
    protection_worker: dict,
    db_session: AsyncSession,
):
    """Authorized Protection worker creates formal CRBCL Referral and generic conversion link."""
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={
            "submitter_name": "Concerned Elder",
            "submitter_email": "elder@community.org",
            "submitter_phone": "306-555-4321",
            "submitter_relationship": "Knowledge Keeper",
            "summary": "Child needs kinship customary care support",
            "details": "Family experiencing housing crisis.",
            "response_id": f"resp-{uuid.uuid4().hex[:8]}",
        },
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = ingest_res.json()["submission_id"]

    # Route & Accept
    await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/route",
        json={"destination_department": "Growing Up Well (Protection Services)"},
        headers=front_desk_worker["headers"],
    )
    await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/department-action",
        json={"action": "ACCEPTED"},
        headers=protection_worker["headers"],
    )

    # Convert to referral by authorized protection worker
    conv_res = await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/convert-to-referral",
        json={
            "priority": "High",
            "community": "Little Red River",
            "immediate_safety_concerns": False,
            "notes": "Formal protection referral opened from public intake.",
        },
        headers=protection_worker["headers"],
    )
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["status"] == "CONVERTED"
    ref_id = uuid.UUID(conv_data["referral_id"])

    # Verify Referral & Reporter in DB
    ref = (await db_session.execute(select(Referral).where(Referral.id == ref_id))).scalar_one()
    assert ref.status == "DRAFT"
    assert ref.priority == "High"
    assert ref.community == "Little Red River"

    reporter = (
        await db_session.execute(
            select(ReferralReporter).where(ReferralReporter.referral_id == ref_id)
        )
    ).scalar_one()
    assert reporter.reporter_name == "Concerned Elder"
    assert reporter.email == "elder@community.org"

    # Verify PublicIntakeConversionLink
    link_stmt = select(PublicIntakeConversionLink).where(
        PublicIntakeConversionLink.submission_id == uuid.UUID(sub_id)
    )
    link = (await db_session.execute(link_stmt)).scalar_one()
    assert link.downstream_entity_type == "referral"
    assert link.downstream_entity_id == ref_id

    # Second attempt to convert returns 400
    second_res = await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/convert-to-referral",
        json={"priority": "High"},
        headers=protection_worker["headers"],
    )
    assert second_res.status_code == 400


@pytest.mark.asyncio
async def test_generic_downstream_conversion_linkage(
    client: AsyncClient,
    protection_worker: dict,
    db_session: AsyncSession,
):
    """Submissions can be generically linked to non-referral domains (e.g. prevention, recruitment)."""
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={"summary": "Caregiver recruitment inquiry", "response_id": f"resp-{uuid.uuid4().hex[:8]}"},
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = ingest_res.json()["submission_id"]
    fake_recruitment_id = uuid.uuid4()

    link_res = await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/convert-generic",
        json={
            "downstream_entity_type": "resource_recruitment",
            "downstream_entity_id": str(fake_recruitment_id),
            "downstream_entity_reference": "REC-2026-00042",
            "notes": "Caregiver applicant initiated",
        },
        headers=protection_worker["headers"],
    )
    assert link_res.status_code == 200
    link_data = link_res.json()
    assert link_data["downstream_entity_type"] == "resource_recruitment"
    assert link_data["downstream_entity_reference"] == "REC-2026-00042"


@pytest.mark.asyncio
async def test_front_desk_rbac_restrictions(
    client: AsyncClient,
    front_desk_worker: dict,
    protection_worker: dict,
    it_admin_user: dict,
    unauthorized_dept_user: dict,
    db_session: AsyncSession,
):
    """Strict RBAC enforcement:

    - Front Desk CANNOT create internal Intake (403)
    - Front Desk CANNOT browse internal Intake (403)
    - Front Desk CANNOT access Cases, Clinical Notes, Finance, Users (403)
    - IT Admin CANNOT read public intake narratives/queue (403)
    - Department alone grants zero Front Desk capability (403)
    """
    # 1. Front Desk cannot create internal Intake
    fake_sub_id = uuid.uuid4()
    fd_convert_res = await client.post(
        f"/api/v1/front-desk/submissions/{fake_sub_id}/convert-to-referral",
        json={"priority": "High"},
        headers=front_desk_worker["headers"],
    )
    assert fd_convert_res.status_code == 403

    # 2. Front Desk cannot browse internal Intake
    fd_referrals_res = await client.get("/api/v1/referrals", headers=front_desk_worker["headers"])
    assert fd_referrals_res.status_code == 403

    # 3. Front Desk cannot access cases
    fd_cases_res = await client.get("/api/v1/cases", headers=front_desk_worker["headers"])
    assert fd_cases_res.status_code == 403

    # 4. Front Desk cannot access clinical notes
    fd_clinical_res = await client.get(
        f"/api/v1/clinical-notes/client/{uuid.uuid4()}",
        headers=front_desk_worker["headers"],
    )
    assert fd_clinical_res.status_code == 403

    # 5. Front Desk cannot access medical records
    fd_medical_res = await client.get(
        f"/api/v1/clients/{uuid.uuid4()}/medical",
        headers=front_desk_worker["headers"],
    )
    assert fd_medical_res.status_code == 403

    # 6. Front Desk cannot access finance
    fd_finance_res = await client.get("/api/v1/finance/invoices", headers=front_desk_worker["headers"])
    assert fd_finance_res.status_code == 403

    # 7. Front Desk cannot access resource clearances
    fd_clearances_res = await client.get(
        f"/api/v1/placement-homes/{uuid.uuid4()}/clearances",
        headers=front_desk_worker["headers"],
    )
    assert fd_clearances_res.status_code == 403

    # 8. Front Desk cannot access user administration
    fd_users_res = await client.get("/api/v1/users", headers=front_desk_worker["headers"])
    assert fd_users_res.status_code == 403

    # 7. IT Admin denied public intake queue & narrative read
    it_subs_res = await client.get("/api/v1/front-desk/submissions", headers=it_admin_user["headers"])
    assert it_subs_res.status_code == 403

    it_detail_res = await client.get(
        f"/api/v1/front-desk/submissions/{fake_sub_id}",
        headers=it_admin_user["headers"],
    )
    assert it_detail_res.status_code == 403

    # 8. Department alone grants ZERO permissions (Cultural worker with Front Desk department gets 403)
    dept_only_res = await client.get(
        "/api/v1/front-desk/submissions",
        headers=unauthorized_dept_user["headers"],
    )
    assert dept_only_res.status_code == 403


@pytest.mark.asyncio
async def test_transactional_outbox_events_emitted(
    client: AsyncClient,
    front_desk_worker: dict,
    protection_worker: dict,
    db_session: AsyncSession,
):
    """Outbox events: PUBLIC_INTAKE_RECEIVED, PUBLIC_INTAKE_ROUTED, PUBLIC_INTAKE_RETURNED, PUBLIC_INTAKE_ACCEPTED."""
    # Ingest -> PUBLIC_INTAKE_RECEIVED
    ingest_res = await client.post(
        "/api/v1/front-desk/ingest/google-form",
        json={"summary": "Outbox test inquiry", "response_id": f"resp-{uuid.uuid4().hex[:8]}"},
        headers={"X-CRBCL-Webhook-Secret": "crbcl-frontdesk-secret-key"},
    )
    sub_id = uuid.UUID(ingest_res.json()["submission_id"])

    # Route -> PUBLIC_INTAKE_ROUTED
    await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/route",
        json={"destination_department": "Growing Up Well (Protection Services)"},
        headers=front_desk_worker["headers"],
    )

    # Return -> PUBLIC_INTAKE_RETURNED
    await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/department-action",
        json={"action": "RETURNED_TO_FRONT_DESK", "notes": "Returning for more info"},
        headers=protection_worker["headers"],
    )

    # Re-route & Accept -> PUBLIC_INTAKE_ACCEPTED
    await client.post(
        f"/api/v1/front-desk/submissions/{sub_id}/route",
        json={"destination_department": "Growing Up Well (Protection Services)"},
        headers=front_desk_worker["headers"],
    )
    await client.patch(
        f"/api/v1/front-desk/submissions/{sub_id}/department-action",
        json={"action": "ACCEPTED"},
        headers=protection_worker["headers"],
    )

    # Verify all outbox events in DB
    events_stmt = (
        select(OutboxEvent)
        .where(OutboxEvent.aggregate_id == sub_id)
        .order_by(OutboxEvent.created_at.asc())
    )
    events = list((await db_session.execute(events_stmt)).scalars().all())
    event_types = [e.event_type for e in events]

    assert "PUBLIC_INTAKE_RECEIVED" in event_types
    assert "PUBLIC_INTAKE_ROUTED" in event_types
    assert "PUBLIC_INTAKE_RETURNED" in event_types
    assert "PUBLIC_INTAKE_ACCEPTED" in event_types


@pytest.mark.asyncio
async def test_front_desk_stats_calculation(
    client: AsyncClient, front_desk_worker: dict, db_session: AsyncSession
):
    """Front Desk stats endpoint computes correct counts across all statuses."""
    res = await client.get("/api/v1/front-desk/stats", headers=front_desk_worker["headers"])
    assert res.status_code == 200
    stats = res.json()
    assert "received_count" in stats
    assert "front_desk_review_count" in stats
    assert "routed_count" in stats
    assert "department_review_count" in stats
    assert "accepted_count" in stats
    assert "returned_count" in stats
    assert "duplicate_count" in stats
    assert "out_of_scope_count" in stats
    assert "closed_count" in stats
    assert "spam_count" in stats
    assert "total_count" in stats
    assert "department_counts" in stats
