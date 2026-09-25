"""Regression test suite for CRBCL Technical Privacy and Security Controls (Section 19).

Covers all 27 mandatory technical regression controls:
 1. Front Desk denied medical
 2. Front Desk denied clinical
 3. Front Desk denied Case
 4. Front Desk denied background checks
 5. Navigator denied medical
 6. Navigator denied clinical
 7. Navigator denied background checks
 8. Navigator denied restricted Case
 9. IT Admin denied Person
10. IT Admin denied Client operational dossier
11. IT Admin denied Intake narratives
12. IT Admin denied HR dossier
13. Board denied Person
14. Board denied Client
15. Board denied Case
16. Board denied medical
17. HR Staff denied Client health
18. Finance denied medical
19. CLIENT_APPROVE alone does not reveal medical
20. restricted-case isolation remains enforced
21. signed document tampering fails
22. expired signed document fails
23. non-clean document download fails
24. duplicate Person search doesn't expose photo
25. Reporter privacy boundaries remain enforced
26. permission checks cannot be bypassed with frontend payloads
27. role/department does not substitute for permission where capability is required
"""

from __future__ import annotations

import hmac
import time
import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core.seed import ROLE_PERMISSIONS_MAP
from app.models.case import Case
from app.models.case_management import CasePerson, CaseRestriction
from app.models.client import Client
from app.models.document import Document
from app.models.front_desk import FrontDeskSubmission
from app.models.medical import ClientMedicalProfile
from app.models.person import Person
from app.models.referral import Referral, ReferralReporter
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import TeamMembership
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.file_security import SECRET_KEY


async def _create_user_with_role(
    db_session: AsyncSession,
    role_key: str,
    email: str,
    full_name: str,
    department: str | None = None,
) -> dict:
    """Helper to provision a test user assigned to an explicit operational role."""
    res = await db_session.execute(select(Role).where(Role.key == role_key))
    role = res.scalars().first()
    if not role:
        role = Role(key=role_key, name=role_key.replace("_", " ").title(), is_system=True)
        db_session.add(role)
        await db_session.flush()

    perm_keys = ROLE_PERMISSIONS_MAP.get(role_key, [])
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
async def sample_client(db_session: AsyncSession, caseworker_user: dict) -> Client:
    p = Person(
        person_id_number="1199990001",
        first_name="Synthetic",
        last_name="PrivacyChild",
        date_of_birth=date(2015, 3, 10),
        created_by=caseworker_user["user"].id,
    )
    db_session.add(p)
    await db_session.flush()

    c = Client(
        person_id=p.id,
        first_name=p.first_name,
        last_name=p.last_name,
        date_of_birth=p.date_of_birth,
        approval_status="APPROVED",
        status="Active",
        created_by=caseworker_user["user"].id,
    )
    db_session.add(c)
    await db_session.commit()
    return c


@pytest.fixture
async def front_desk_user(db_session: AsyncSession, seed_roles_and_permissions) -> dict:
    return await _create_user_with_role(
        db_session,
        role_key="front_desk",
        email="frontdesk.test@crbcl.ca",
        full_name="Fiona FrontDesk",
        department="Front Desk & Navigation",
    )


@pytest.fixture
async def resource_supervisor_user(db_session: AsyncSession, seed_roles_and_permissions) -> dict:
    return await _create_user_with_role(
        db_session,
        role_key="resource_supervisor",
        email="res_sup.test@crbcl.ca",
        full_name="Ray ResourceSupervisor",
        department="Resource Unit",
    )


# ── Tests 1 - 4: Front Desk Boundaries ──────────────────────────────────────────


@pytest.mark.anyio
async def test_01_front_desk_denied_medical(client: AsyncClient, front_desk_user: dict, sample_client: Client):
    """1. Front Desk cannot read client medical data."""
    res = await client.get(f"/api/v1/clients/{sample_client.id}/medical", headers=front_desk_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_02_front_desk_denied_clinical(client: AsyncClient, front_desk_user: dict, sample_client: Client):
    """2. Front Desk cannot read clinical / LPN notes."""
    res = await client.get(
        f"/api/v1/clinical-notes/client/{sample_client.id}",
        headers=front_desk_user["headers"],
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_03_front_desk_denied_case(client: AsyncClient, front_desk_user: dict):
    """3. Front Desk cannot access Case management records."""
    res = await client.get("/api/v1/cases", headers=front_desk_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_04_front_desk_denied_background_checks(client: AsyncClient, front_desk_user: dict):
    """4. Front Desk cannot access background checks or clearances."""
    res = await client.get("/api/v1/background-checks", headers=front_desk_user["headers"])
    assert res.status_code == 403
    assert "permission" in res.text.lower() or "background_check" in res.text.lower()


# ── Tests 5 - 8: Navigator Boundaries ──────────────────────────────────────────


@pytest.mark.anyio
async def test_05_navigator_denied_medical(client: AsyncClient, navigator_user: dict, sample_client: Client):
    """5. Navigator cannot read client medical information."""
    res = await client.get(f"/api/v1/clients/{sample_client.id}/medical", headers=navigator_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_06_navigator_denied_clinical(client: AsyncClient, navigator_user: dict, sample_client: Client):
    """6. Navigator cannot read clinical notes."""
    res = await client.get(
        f"/api/v1/clinical-notes/client/{sample_client.id}",
        headers=navigator_user["headers"],
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_07_navigator_denied_background_checks(client: AsyncClient, navigator_user: dict):
    """7. Navigator cannot read background checks."""
    res = await client.get("/api/v1/background-checks", headers=navigator_user["headers"])
    assert res.status_code == 403
    assert "permission" in res.text.lower() or "background_check" in res.text.lower()


@pytest.mark.anyio
async def test_08_navigator_denied_restricted_case(client: AsyncClient, navigator_user: dict):
    """8. Navigator cannot access Case operational dossiers."""
    res = await client.get("/api/v1/cases", headers=navigator_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


# ── Tests 9 - 12: IT Admin Boundaries ──────────────────────────────────────────


@pytest.mark.anyio
async def test_09_it_admin_denied_person(client: AsyncClient, it_admin_user: dict):
    """9. IT Admin cannot access canonical Person records."""
    res = await client.get("/api/v1/persons", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] in ("ROLE_ACCESS_DENIED", "PERMISSION_DENIED")


@pytest.mark.anyio
async def test_10_it_admin_denied_client_operational_dossier(client: AsyncClient, it_admin_user: dict):
    """10. IT Admin cannot access Client operational dossiers."""
    res = await client.get("/api/v1/clients", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_11_it_admin_denied_intake_narratives(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """11. IT Admin cannot access Intake and Public Submission narratives."""
    sub = FrontDeskSubmission(
        submission_number="FDS-2026-NARRATIVE",
        source="phone",
        status="RECEIVED",
        urgency="High",
        submitter_name="Confidential Submitter",
        summary="Child protection intake narrative.",
    )
    db_session.add(sub)
    await db_session.commit()

    res = await client.get(f"/api/v1/front-desk/submissions/{sub.id}", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"

    ref_res = await client.get("/api/v1/referrals", headers=it_admin_user["headers"])
    assert ref_res.status_code == 403
    assert ref_res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_12_it_admin_denied_hr_dossier(client: AsyncClient, it_admin_user: dict):
    """12. IT Admin cannot access HR employee dossiers or HR Dashboard."""
    res = await client.get("/api/v1/org-ops/hr-dashboard", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


# ── Tests 13 - 16: Board Member Boundaries ──────────────────────────────────────


@pytest.mark.anyio
async def test_13_board_denied_person(client: AsyncClient, board_member_user: dict):
    """13. Board Member cannot access canonical Person records."""
    res = await client.get("/api/v1/persons", headers=board_member_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] in ("ROLE_ACCESS_DENIED", "PERMISSION_DENIED")


@pytest.mark.anyio
async def test_14_board_denied_client(client: AsyncClient, board_member_user: dict):
    """14. Board Member cannot access Client operational dossiers."""
    res = await client.get("/api/v1/clients", headers=board_member_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_15_board_denied_case(client: AsyncClient, board_member_user: dict):
    """15. Board Member cannot access individual Case files."""
    res = await client.get("/api/v1/cases", headers=board_member_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_16_board_denied_medical(client: AsyncClient, board_member_user: dict, sample_client: Client):
    """16. Board Member cannot access individual Client health data."""
    res = await client.get(f"/api/v1/clients/{sample_client.id}/medical", headers=board_member_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


# ── Tests 17 - 19: Cross-Domain Health Segregation ─────────────────────────────


@pytest.mark.anyio
async def test_17_hr_staff_denied_client_health(client: AsyncClient, hr_user: dict, sample_client: Client):
    """17. HR Staff cannot access child/client health or medical records."""
    res = await client.get(f"/api/v1/clients/{sample_client.id}/medical", headers=hr_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_18_finance_denied_medical(client: AsyncClient, finance_user: dict, sample_client: Client):
    """18. Finance Staff cannot read client medical information."""
    res = await client.get(f"/api/v1/clients/{sample_client.id}/medical", headers=finance_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_19_client_approve_alone_does_not_reveal_medical(
    client: AsyncClient, db_session: AsyncSession, sample_client: Client
):
    """19. Possessing client.approve (without client.medical.read) does not grant medical access.
    Explicitly tests:
    - Actor with CLIENT_READ + CLIENT_APPROVE (strictly NO CLIENT_MEDICAL_READ)
    - Approval queue works (200 OK)
    - Client approval review works as intended, but protected medical subsection remains omitted (None)
    - Direct client medical endpoint strictly returns 403 Forbidden.
    """
    lim_user = User(
        email="limited-approver-p19@crbcl.ca",
        email_normalized="limited-approver-p19@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Limited Approver Privacy",
        is_active=True,
        is_verified=True,
    )
    db_session.add(lim_user)
    await db_session.flush()

    lim_role = Role(key="limited_approver_p19", name="Limited Approver P19", is_system=False)
    db_session.add(lim_role)
    await db_session.flush()

    p_app = (await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_APPROVE.value))).scalar_one()
    p_read = (await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_READ.value))).scalar_one()

    db_session.add(RolePermission(role_id=lim_role.id, permission_id=p_app.id))
    db_session.add(RolePermission(role_id=lim_role.id, permission_id=p_read.id))
    db_session.add(UserRole(user_id=lim_user.id, role_id=lim_role.id))
    await db_session.commit()

    lim_token = create_access_token(lim_user.id)
    lim_headers = {"Authorization": f"Bearer {lim_token}"}

    # Seed a pending proposal with a medical profile
    p_pending = Person(
        person_id_number="1199990055",
        first_name="PendingProposal",
        last_name="ReviewChild",
        date_of_birth=date(2016, 5, 15),
        created_by=lim_user.id,
    )
    db_session.add(p_pending)
    await db_session.flush()

    c_pending = Client(
        person_id=p_pending.id,
        first_name=p_pending.first_name,
        last_name=p_pending.last_name,
        date_of_birth=p_pending.date_of_birth,
        approval_status="PENDING_APPROVAL",
        status="Inactive",
        submitted_by=lim_user.id,
        created_by=lim_user.id,
    )
    db_session.add(c_pending)
    await db_session.flush()

    med = ClientMedicalProfile(
        client_id=c_pending.id,
        general_notes="Confidential clinical notes for pending proposal",
        primary_physician_name="Dr. Specialists Only",
    )
    db_session.add(med)
    await db_session.commit()

    # 1. Approval queue is accessible to client approver
    pending_res = await client.get("/api/v1/clients/approvals/pending", headers=lim_headers)
    assert pending_res.status_code == 200

    # 2. Review endpoint succeeds, but medical subsection remains omitted (None)
    rev_res = await client.get(f"/api/v1/clients/approvals/{c_pending.id}", headers=lim_headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["client"]["id"] == str(c_pending.id)
    assert rev_res.json()["person"]["medical"] is None

    # 3. Direct medical endpoint strictly denied with 403 Forbidden
    med_res = await client.get(f"/api/v1/clients/{c_pending.id}/medical", headers=lim_headers)
    assert med_res.status_code == 403
    assert med_res.json()["error"]["code"] == "PERMISSION_DENIED"


# ── Test 20: Restricted Case Isolation ─────────────────────────────────────────


@pytest.mark.anyio
async def test_20_restricted_case_isolation_remains_enforced(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict, supervisor_user: dict
):
    """20. Active conflict-of-interest case restriction blocks user from reading case and associated Person."""
    case = Case(
        case_number="CASE-2026-PRIVACY-RESTRICT",
        title="Conflict of Interest Protected Family Case",
        status="OPEN",
        case_type="PROTECTION",
    )
    db_session.add(case)
    await db_session.flush()

    person = Person(
        person_id_number="1199990099",
        first_name="RestrictedChild",
        last_name="Private",
        created_by=supervisor_user["user"].id,
    )
    db_session.add(person)
    await db_session.flush()

    cp = CasePerson(case_id=case.id, person_id=person.id, role="subject_child")
    db_session.add(cp)

    restr = CaseRestriction(
        case_id=case.id,
        user_id=caseworker_user["user"].id,
        restriction_type="conflict_of_interest",
        reason="Personal relationship with extended family",
        is_active=True,
    )
    db_session.add(restr)
    await db_session.commit()

    # Case endpoint blocked for restricted caseworker
    case_res = await client.get(f"/api/v1/cases/{case.id}", headers=caseworker_user["headers"])
    assert case_res.status_code == 403

    # Person endpoint blocked for restricted caseworker (cannot bypass via canonical Person)
    person_res = await client.get(f"/api/v1/persons/{person.id}", headers=caseworker_user["headers"])
    assert person_res.status_code == 403
    assert person_res.json()["error"]["code"] == "CASE_RESTRICTION_ACTIVE"


# ── Tests 21 - 23: Document Security & HMAC ────────────────────────────────────


@pytest.mark.anyio
async def test_21_signed_document_tampering_fails(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """21. Tampered signature and document-ID mismatch on signed document download return 403 Forbidden."""
    doc1 = Document(
        filename="assessment_doc1.pdf",
        original_filename="assessment_doc1.pdf",
        size_bytes=2048,
        content_type="application/pdf",
        storage_path="documents/test1.pdf",
        scan_status="clean",
        created_by=caseworker_user["user"].id,
    )
    doc2 = Document(
        filename="assessment_doc2.pdf",
        original_filename="assessment_doc2.pdf",
        size_bytes=2048,
        content_type="application/pdf",
        storage_path="documents/test2.pdf",
        scan_status="clean",
        created_by=caseworker_user["user"].id,
    )
    db_session.add_all([doc1, doc2])
    await db_session.commit()

    expires = int(time.time()) + 900

    # A. Tampered signature on doc1 fails
    res_tampered = await client.get(f"/api/v1/documents/{doc1.id}/download?expires={expires}&sig=invalid_tampered_sig")
    assert res_tampered.status_code == 403

    # B. Document-ID / signature mismatch fails (valid sig for doc1 used for doc2)
    sig_doc1 = hmac.new(SECRET_KEY.encode(), f"{doc1.id}:{expires}".encode(), "sha256").hexdigest()
    res_mismatch = await client.get(f"/api/v1/documents/{doc2.id}/download?expires={expires}&sig={sig_doc1}")
    assert res_mismatch.status_code == 403


@pytest.mark.anyio
async def test_22_expired_signed_document_fails(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """22. Expired signed document link returns 403 Forbidden."""
    doc = Document(
        filename="assessment.pdf",
        original_filename="assessment.pdf",
        size_bytes=2048,
        content_type="application/pdf",
        storage_path="documents/test.pdf",
        scan_status="clean",
        created_by=caseworker_user["user"].id,
    )
    db_session.add(doc)
    await db_session.commit()

    past_expires = int(time.time()) - 100
    sig_base = f"{doc.id}:{past_expires}"
    valid_past_sig = hmac.new(SECRET_KEY.encode(), sig_base.encode(), "sha256").hexdigest()

    res = await client.get(f"/api/v1/documents/{doc.id}/download?expires={past_expires}&sig={valid_past_sig}")
    assert res.status_code == 403


@pytest.mark.anyio
async def test_23_non_clean_document_download_fails(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """23. Only documents with scan_status 'clean' release bytes; pending, infected, failed, quarantined all fail.
    Authorized flow with scan_status 'clean' succeeds and releases file bytes.
    """
    expires = int(time.time()) + 900
    non_clean_statuses = ["quarantined", "pending", "infected", "failed", "error"]

    # Verify all non-clean scan statuses are rejected with 403
    for st in non_clean_statuses:
        doc = Document(
            filename=f"doc_{st}.pdf",
            original_filename=f"doc_{st}.pdf",
            size_bytes=4096,
            content_type="application/pdf",
            storage_path=f"documents/doc_{st}.pdf",
            scan_status=st,
            created_by=caseworker_user["user"].id,
        )
        db_session.add(doc)
        await db_session.commit()

        sig = hmac.new(SECRET_KEY.encode(), f"{doc.id}:{expires}".encode(), "sha256").hexdigest()
        res = await client.get(f"/api/v1/documents/{doc.id}/download?expires={expires}&sig={sig}")
        assert res.status_code == 403
        assert "security scan" in res.text.lower()

    # Verify authorized flow: valid clean document releases bytes
    from app.storage.service import StorageService

    storage_svc = StorageService(db_session)
    clean_doc = await storage_svc.store_document(
        filename="verified_clean_doc.pdf",
        content=b"%PDF-1.4 synthetic secure payload bytes for clean document test",
        content_type="application/pdf",
        uploaded_by=caseworker_user["user"].id,
    )
    clean_doc.scan_status = "clean"
    await db_session.commit()

    sig_clean = hmac.new(SECRET_KEY.encode(), f"{clean_doc.id}:{expires}".encode(), "sha256").hexdigest()
    res_clean = await client.get(f"/api/v1/documents/{clean_doc.id}/download?expires={expires}&sig={sig_clean}")
    assert res_clean.status_code == 200
    assert res_clean.content == b"%PDF-1.4 synthetic secure payload bytes for clean document test"


# ── Test 24: Duplicate Person Search Minimization ──────────────────────────────


@pytest.mark.anyio
async def test_24_duplicate_person_search_does_not_expose_photo(
    client: AsyncClient, caseworker_user: dict, sample_client: Client
):
    """24. Canonical Person search results disclose limited matching fields and omit profile photo."""
    res = await client.get("/api/v1/persons?query=Synthetic", headers=caseworker_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "first_name" in item
    assert "last_name" in item
    assert "person_id_number" in item
    # Verified: photo_url is excluded from PersonSearchResultResponse
    assert "photo_url" not in item


# ── Test 25: Reporter Privacy Boundary ─────────────────────────────────────────


@pytest.mark.anyio
async def test_25_reporter_privacy_boundaries_remain_enforced(
    client: AsyncClient, db_session: AsyncSession, seed_roles_and_permissions: dict
):
    """25. Reporter identity is segregated and requires intake.reporter.read."""
    # User with intake.read but WITHOUT intake.reporter.read
    role_key = "test_intake_reader_no_reporter"
    role = Role(key=role_key, name="Intake Reader", is_system=False)
    db_session.add(role)
    await db_session.flush()

    p_res = await db_session.execute(select(Permission).where(Permission.key == Permissions.INTAKE_READ.value))
    p_intake_read = p_res.scalar_one()
    rp = RolePermission(role_id=role.id, permission_id=p_intake_read.id)
    db_session.add(rp)
    await db_session.flush()

    reader_user = User(
        email="intake.reader@crbcl.ca",
        email_normalized="intake.reader@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Ian IntakeReader",
        is_active=True,
        is_verified=True,
    )
    db_session.add(reader_user)
    await db_session.flush()

    ur = UserRole(user_id=reader_user.id, role_id=role.id)
    db_session.add(ur)

    # Seed referral with reporter
    ref = Referral(
        referral_number="REF-2026-REPORTER-SEC",
        status="RECEIVED",
        received_date=date.today(),
        summary="Community safety inquiry.",
    )
    db_session.add(ref)
    await db_session.flush()

    rep = ReferralReporter(
        referral_id=ref.id,
        reporter_name="Confidential Informant",
        phone="306-555-0199",
        email="informant@secret.org",
        relationship_to_family="Neighbor",
    )
    db_session.add(rep)
    await db_session.commit()

    token = create_access_token(reader_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Referral detail without intake.reporter.read redacts confidential reporter details
    rep_res = await client.get(f"/api/v1/referrals/{ref.id}", headers=headers)
    assert rep_res.status_code == 200
    rep_data = rep_res.json()["reporter"]
    assert rep_data is not None
    assert rep_data["is_redacted"] is True
    assert rep_data["reporter_name"] == "[CONFIDENTIAL / REDACTED]"
    assert rep_data["phone"] is None
    assert rep_data["email"] is None

    # 2. Granting intake.reporter.read permits retrieval of full confidential reporter identity
    p_rep_res = await db_session.execute(select(Permission).where(Permission.key == Permissions.INTAKE_REPORTER_READ.value))
    p_intake_rep = p_rep_res.scalar_one()
    rp_auth = RolePermission(role_id=role.id, permission_id=p_intake_rep.id)
    db_session.add(rp_auth)
    await db_session.commit()

    auth_res = await client.get(f"/api/v1/referrals/{ref.id}", headers=headers)
    assert auth_res.status_code == 200
    auth_rep = auth_res.json()["reporter"]
    assert auth_rep is not None
    assert auth_rep["is_redacted"] is False
    assert auth_rep["reporter_name"] == "Confidential Informant"
    assert auth_rep["phone"] == "306-555-0199"
    assert auth_rep["email"] == "informant@secret.org"
    assert auth_rep["relationship_to_family"] == "Neighbor"

    # 3. User with NO intake permission is denied access to referral entirely (HTTP 403)
    no_perm_user = User(
        email="unpermitted.intake@crbcl.ca",
        email_normalized="unpermitted.intake@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Unpermitted User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(no_perm_user)
    await db_session.commit()

    unauth_token = create_access_token(no_perm_user.id)
    unauth_res = await client.get(f"/api/v1/referrals/{ref.id}", headers={"Authorization": f"Bearer {unauth_token}"})
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error"]["code"] == "PERMISSION_DENIED"


# ── Test 26: Frontend Payload Manipulation ─────────────────────────────────────


@pytest.mark.anyio
async def test_26_permission_checks_cannot_be_bypassed_with_frontend_payloads(
    client: AsyncClient, caseworker_user: dict, sample_client: Client
):
    """26. Malicious frontend payloads attempting to inject administrative role claims cannot elevate permissions."""
    forged_approval_payload = {
        "is_admin": True,
        "roles": ["ceo", "executive_director", "supervisor"],
        "permissions": ["client.approve", "client.medical.read"],
        "reason": "Forged bypass attempt",
    }
    # Caseworker cannot approve client even if frontend payload sends fake roles/perms
    res = await client.post(
        f"/api/v1/clients/approvals/{sample_client.id}/approve",
        json=forged_approval_payload,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


# ── Test 27: Department Separation ─────────────────────────────────────────────


@pytest.mark.anyio
async def test_27_role_or_department_does_not_substitute_for_permission(
    client: AsyncClient, db_session: AsyncSession
):
    """27. Department assignment alone (e.g. 'Child Safety') does not substitute for missing capability."""
    # User belongs to Child Safety department but holds no permissions
    dept_user = User(
        email="unprivileged.dept@crbcl.ca",
        email_normalized="unprivileged.dept@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Dan DepartmentOnly",
        department="Child Safety (Protection)",
        is_active=True,
        is_verified=True,
    )
    db_session.add(dept_user)
    await db_session.commit()

    token = create_access_token(dept_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res_clients = await client.get("/api/v1/clients", headers=headers)
    assert res_clients.status_code == 403

    res_cases = await client.get("/api/v1/cases", headers=headers)
    assert res_cases.status_code == 403

    res_intake = await client.get("/api/v1/referrals", headers=headers)
    assert res_intake.status_code == 403
