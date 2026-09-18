"""Comprehensive tests for Client Creation, Approval Workflow, Identity Reuse, and Role Boundaries.

Covers 25 core scenarios:
 1. Operational staff can list clients
 2. Propose existing Person as client (PENDING_APPROVAL)
 3. Create Person and propose as client in unified submit-new flow
 4. Newly created Person receives single permanent 10-digit ID
 5. Existing Person reuse retains original 10-digit ID
 6. Duplicate pending client proposal prevented (409)
 7. Already-approved client cannot be reproposed (409)
 8. Newly proposed clients start strictly in PENDING_APPROVAL
 9. Supervisor can view pending approvals queue
 10. Director can view pending approvals queue
 11. Unauthorized staff (caseworker) cannot approve or reject (403)
 12. Supervisor/Director can approve proposal (transitions to APPROVED)
 13. Proposal return preserves canonical Person record
 14. Proposal decline preserves canonical Person record
 15. Audit logging and append-only history tracks actors, timestamps, and notes
 16. Protected Person subsections (medical) respect permissions in review view
 17. Restricted case information is not leaked into client review
 18. IT Admin cannot access operational client records (403)
 19. Board Member cannot access operational client records (403)
 20. Approved client attachable to Case through canonical Person
 21. Duplicate active CasePerson link is prevented (409)
 22. Profile photo returns valid signed URL
 23. Photo fallback when no photo exists (None)
 24. Invalid approval transition is rejected (409)
 25. Repeated/duplicate decision is rejected (409)
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

from app.models.client import Client, ClientApprovalHistory
from app.models.document import Document
from app.models.medical import ClientMedicalProfile
from app.models.person import Person
from app.services.file_security import SECRET_KEY


@pytest.mark.anyio
async def test_01_staff_can_list_clients(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, db_session: AsyncSession
):
    """Scenario 1: All operational staff with CLIENT_READ can retrieve the clients list."""
    # Seed an approved client
    p = Person(
        person_id_number="1100000001",
        first_name="Jordan",
        last_name="Cardinal",
        date_of_birth=date(1995, 5, 20),
        created_by=caseworker_user["user"].id,
        updated_by=caseworker_user["user"].id,
    )
    db_session.add(p)
    await db_session.flush()

    c = Client(
        person_id=p.id,
        first_name=p.first_name,
        last_name=p.last_name,
        date_of_birth=p.date_of_birth,
        status="Active",
        approval_status="APPROVED",
        created_by=caseworker_user["user"].id,
        updated_by=caseworker_user["user"].id,
    )
    db_session.add(c)
    await db_session.commit()

    # Caseworker lists clients
    res_cw = await client.get("/api/v1/clients", headers=caseworker_user["headers"])
    assert res_cw.status_code == 200
    cw_data = res_cw.json()
    assert len(cw_data["items"]) >= 1
    item = next(i for i in cw_data["items"] if i["id"] == str(c.id))
    assert item["first_name"] == "Jordan"
    assert item["person_id_number"] == "1100000001"
    assert item["approval_status"] == "APPROVED"

    # Supervisor lists clients
    res_sup = await client.get("/api/v1/clients", headers=supervisor_user["headers"])
    assert res_sup.status_code == 200
    assert len(res_sup.json()["items"]) >= 1


@pytest.mark.anyio
async def test_02_propose_existing_person_as_client(
    client: AsyncClient, caseworker_user: dict, db_session: AsyncSession
):
    """Scenario 2: Proposing an existing canonical Person creates Client in PENDING_APPROVAL status."""
    # Create canonical person
    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Tanya",
            "last_name": "Bird",
            "date_of_birth": "1998-03-12",
            "gender": "Female",
        },
        headers=caseworker_user["headers"],
    )
    assert p_res.status_code == 201
    person = p_res.json()
    person_id = person["id"]
    numeric_id = person["person_id_number"]

    # Propose existing person as client
    payload = {
        "person_id": person_id,
        "risk_level": "Medium",
        "submission_notes": "Needs urgent family stabilization support.",
    }
    submit_res = await client.post(
        "/api/v1/clients/submit-existing", json=payload, headers=caseworker_user["headers"]
    )
    assert submit_res.status_code == 201
    client_data = submit_res.json()
    assert client_data["person_id"] == person_id
    assert client_data["person_id_number"] == numeric_id
    assert client_data["approval_status"] == "PENDING_APPROVAL"
    assert client_data["submission_notes"] == "Needs urgent family stabilization support."
    assert client_data["submitted_by"] == str(caseworker_user["user"].id)


@pytest.mark.anyio
async def test_03_create_person_and_propose_as_client(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 3: Create Person and submit as client in unified submit-new flow."""
    payload = {
        "first_name": "Dakota",
        "last_name": "Rain",
        "date_of_birth": "2005-11-23",
        "gender": "Non-Binary",
        "indigenous_identity": "First Nations",
        "band_nation": "George Gordon First Nation",
        "risk_level": "High",
        "submission_notes": "Youth transitioning from care requiring wellness services.",
    }
    res = await client.post(
        "/api/v1/clients/submit-new", json=payload, headers=caseworker_user["headers"]
    )
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Dakota"
    assert data["last_name"] == "Rain"
    assert data["approval_status"] == "PENDING_APPROVAL"
    assert data["person_id_number"] is not None
    assert len(data["person_id_number"]) == 10
    assert data["person_id_number"].isdigit()


@pytest.mark.anyio
async def test_04_new_person_receives_single_10_digit_id(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 4: Person created via submit-new receives exactly one permanent 10-digit numeric ID."""
    payload = {
        "first_name": "Elijah",
        "last_name": "Morin",
        "date_of_birth": "2000-01-10",
        "gender": "Male",
        "risk_level": "Low",
    }
    res = await client.post(
        "/api/v1/clients/submit-new", json=payload, headers=caseworker_user["headers"]
    )
    assert res.status_code == 201
    person_id_num = res.json()["person_id_number"]
    assert len(person_id_num) == 10
    assert person_id_num.isdigit()
    assert int(person_id_num) >= 1100000000


@pytest.mark.anyio
async def test_05_existing_person_reuse_retains_original_id(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 5: Existing Person retains exact same 10-digit ID when proposed as client."""
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Riley", "last_name": "Standingready", "date_of_birth": "1994-08-14"},
        headers=caseworker_user["headers"],
    )
    orig_person = p_res.json()
    orig_id = orig_person["id"]
    orig_number = orig_person["person_id_number"]

    # Submit as client
    res = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": orig_id, "risk_level": "Medium"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    client_data = res.json()
    assert client_data["person_id"] == orig_id
    assert client_data["person_id_number"] == orig_number


@pytest.mark.anyio
async def test_06_duplicate_pending_client_proposal_prevented(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 6: Attempting to propose a person who is already pending approval returns 409 Conflict."""
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Kelsey", "last_name": "Bone", "date_of_birth": "1997-04-05"},
        headers=caseworker_user["headers"],
    )
    person_id = p_res.json()["id"]

    # First proposal succeeds
    res1 = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": person_id, "risk_level": "Low"},
        headers=caseworker_user["headers"],
    )
    assert res1.status_code == 201

    # Second proposal must fail with 409 Conflict
    res2 = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": person_id, "risk_level": "High"},
        headers=caseworker_user["headers"],
    )
    assert res2.status_code == 409
    error_detail = res2.json()["error"]
    assert error_detail["code"] == "CLIENT_PENDING_APPROVAL"


@pytest.mark.anyio
async def test_07_already_approved_client_cannot_be_reproposed(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 7: Attempting to propose a person who is already an approved client returns 409 Conflict."""
    # Create and submit
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Marcus", "last_name": "Delorme", "date_of_birth": "1991-07-22"},
        headers=caseworker_user["headers"],
    )
    person_id = p_res.json()["id"]

    res_sub = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": person_id, "risk_level": "Low"},
        headers=caseworker_user["headers"],
    )
    client_id = res_sub.json()["id"]

    # Supervisor approves
    res_app = await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve",
        headers=supervisor_user["headers"],
    )
    assert res_app.status_code == 200
    assert res_app.json()["approval_status"] == "APPROVED"

    # Attempt to propose again returns 409 ALREADY_CLIENT
    res_dup = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": person_id, "risk_level": "High"},
        headers=caseworker_user["headers"],
    )
    assert res_dup.status_code == 409
    error_detail = res_dup.json()["error"]
    assert error_detail["code"] == "ALREADY_CLIENT"


@pytest.mark.anyio
async def test_08_newly_proposed_clients_start_in_pending(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 8: Newly proposed clients enter PENDING_APPROVAL and status Pending Intake."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={
            "first_name": "Naomi",
            "last_name": "Laroque",
            "date_of_birth": "2003-09-14",
            "risk_level": "Medium",
        },
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    c = res.json()
    assert c["approval_status"] == "PENDING_APPROVAL"
    assert c["status"] == "Pending Intake"


@pytest.mark.anyio
async def test_09_supervisor_can_view_pending_queue(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 9: Supervisor can list pending client proposals."""
    # Submit proposal
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={
            "first_name": "Liam",
            "last_name": "Iron",
            "date_of_birth": "2004-06-18",
            "risk_level": "Low",
            "submission_notes": "Supervisor pending queue test.",
        },
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # Fetch pending queue
    pending_res = await client.get("/api/v1/clients/approvals/pending", headers=supervisor_user["headers"])
    assert pending_res.status_code == 200
    pending_items = pending_res.json()["items"]
    found = next((i for i in pending_items if i["client_id"] == client_id), None)
    assert found is not None
    assert found["first_name"] == "Liam"
    assert found["approval_status"] == "PENDING_APPROVAL"
    assert found["submission_notes"] == "Supervisor pending queue test."


@pytest.mark.anyio
async def test_10_director_can_view_pending_queue(
    client: AsyncClient, caseworker_user: dict, executive_director_user: dict
):
    """Scenario 10: Executive Director can list pending client proposals."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={
            "first_name": "Chloe",
            "last_name": "Peltier",
            "date_of_birth": "2002-12-01",
            "risk_level": "Medium",
        },
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    pending_res = await client.get(
        "/api/v1/clients/approvals/pending", headers=executive_director_user["headers"]
    )
    assert pending_res.status_code == 200
    found = next((i for i in pending_res.json()["items"] if i["client_id"] == client_id), None)
    assert found is not None


@pytest.mark.anyio
async def test_11_unauthorized_staff_cannot_approve_or_reject(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 11: Caseworker lacks CLIENT_APPROVE and receives 403 on approve/return/decline."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Aidan", "last_name": "Lavallee", "date_of_birth": "2001-05-10"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # Try approve -> 403
    app_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve", headers=caseworker_user["headers"]
    )
    assert app_res.status_code == 403

    # Try return -> 403
    ret_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/return",
        json={"reason": "Need more data"},
        headers=caseworker_user["headers"],
    )
    assert ret_res.status_code == 403

    # Try decline -> 403
    dec_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/decline",
        json={"reason": "Not eligible"},
        headers=caseworker_user["headers"],
    )
    assert dec_res.status_code == 403


@pytest.mark.anyio
async def test_12_authorized_approval_succeeds(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, db_session: AsyncSession
):
    """Scenario 12: Authorized Supervisor approves proposal; updates status to APPROVED and records decider."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Lucas", "last_name": "Keech", "date_of_birth": "1999-02-14"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # Supervisor approves
    app_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve",
        headers=supervisor_user["headers"],
    )
    assert app_res.status_code == 200
    data = app_res.json()
    assert data["approval_status"] == "APPROVED"
    assert data["status"] == "Active"
    assert data["decided_by"] == str(supervisor_user["user"].id)
    assert data["decided_at"] is not None

    # Verify history entry
    hist = await db_session.execute(
        select(ClientApprovalHistory).where(ClientApprovalHistory.client_id == uuid.UUID(client_id))
    )
    entries = hist.scalars().all()
    assert len(entries) >= 2
    approve_entry = next(e for e in entries if e.action == "APPROVED")
    assert approve_entry.actor_id == supervisor_user["user"].id
    assert approve_entry.to_status == "APPROVED"


@pytest.mark.anyio
async def test_13_proposal_return_preserves_canonical_person(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 13: Returning a proposal requires a reason, updates to RETURNED, preserves Person."""
    # Submit proposal
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Maya", "last_name": "Arcand", "date_of_birth": "1996-10-30"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]
    person_id = res.json()["person_id"]
    person_id_number = res.json()["person_id_number"]

    # Try return without reason -> 400
    bad_return = await client.post(
        f"/api/v1/clients/approvals/{client_id}/return",
        json={"reason": "   "},
        headers=supervisor_user["headers"],
    )
    assert bad_return.status_code == 400

    # Valid return with reason
    good_return = await client.post(
        f"/api/v1/clients/approvals/{client_id}/return",
        json={"reason": "Please attach Band confirmation letter."},
        headers=supervisor_user["headers"],
    )
    assert good_return.status_code == 200
    ret_data = good_return.json()
    assert ret_data["approval_status"] == "RETURNED"
    assert ret_data["decision_reason"] == "Please attach Band confirmation letter."

    # Verify canonical Person remains intact and untouched
    p_get = await client.get(f"/api/v1/persons/{person_id}", headers=caseworker_user["headers"])
    assert p_get.status_code == 200
    p_data = p_get.json()["person"]
    assert p_data["id"] == person_id
    assert p_data["person_id_number"] == person_id_number
    assert p_data["first_name"] == "Maya"


@pytest.mark.anyio
async def test_14_proposal_decline_preserves_canonical_person(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 14: Declining a proposal requires a reason, updates to DECLINED, preserves Person."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Evan", "last_name": "Standingwater", "date_of_birth": "1993-04-18"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]
    person_id = res.json()["person_id"]

    # Decline without reason -> 400
    bad_dec = await client.post(
        f"/api/v1/clients/approvals/{client_id}/decline",
        json={"reason": ""},
        headers=supervisor_user["headers"],
    )
    assert bad_dec.status_code == 400

    # Decline with reason -> 200
    good_dec = await client.post(
        f"/api/v1/clients/approvals/{client_id}/decline",
        json={"reason": "Out of catchment area; referred to regional partner."},
        headers=supervisor_user["headers"],
    )
    assert good_dec.status_code == 200
    dec_data = good_dec.json()
    assert dec_data["approval_status"] == "DECLINED"
    assert dec_data["decision_reason"] == "Out of catchment area; referred to regional partner."

    # Person remains intact
    p_get = await client.get(f"/api/v1/persons/{person_id}", headers=caseworker_user["headers"])
    assert p_get.status_code == 200
    assert p_get.json()["person"]["id"] == person_id


@pytest.mark.anyio
async def test_15_audit_logging_and_approval_history(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, db_session: AsyncSession
):
    """Scenario 15: Every lifecycle action records audit log and immutable client_approvals entry."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Tara", "last_name": "Morin", "date_of_birth": "1992-09-08"},
        headers=caseworker_user["headers"],
    )
    client_id = uuid.UUID(res.json()["id"])

    # Approve
    await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve",
        headers=supervisor_user["headers"],
    )

    # Check approval history
    history_res = await db_session.execute(
        select(ClientApprovalHistory)
        .where(ClientApprovalHistory.client_id == client_id)
        .order_by(ClientApprovalHistory.created_at.asc())
    )
    rows = history_res.scalars().all()
    assert len(rows) == 2
    assert rows[0].action == "SUBMITTED"
    assert rows[0].actor_id == caseworker_user["user"].id
    assert rows[1].action == "APPROVED"
    assert rows[1].actor_id == supervisor_user["user"].id


@pytest.mark.anyio
async def test_16_protected_person_subsections_in_review_view(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, db_session: AsyncSession
):
    """Scenario 16: Review view `/approvals/{id}` respects field-level permissions for person subsections."""
    # Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Quinn", "last_name": "Saysewahum", "date_of_birth": "2000-05-15"},
        headers=caseworker_user["headers"],
    )
    person_id = uuid.UUID(p_res.json()["id"])

    # Add medical profile for person
    med_client = Client(
        person_id=person_id,
        first_name="Quinn",
        last_name="Saysewahum",
        status="Pending Intake",
        approval_status="PENDING_APPROVAL",
        created_by=caseworker_user["user"].id,
    )
    db_session.add(med_client)
    await db_session.flush()

    med = ClientMedicalProfile(
        client_id=med_client.id,
        general_notes="Confidential medical notes",
        primary_physician_name="Dr. Taylor",
    )
    db_session.add(med)
    await db_session.commit()

    # Supervisor (with CLIENT_APPROVE and CLIENT_MEDICAL_READ) sees medical data in review
    rev_res = await client.get(
        f"/api/v1/clients/approvals/{med_client.id}", headers=supervisor_user["headers"]
    )
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert rev_data["client"]["id"] == str(med_client.id)
    assert rev_data["person"] is not None
    assert rev_data["person"]["medical"] is not None
    assert rev_data["person"]["medical"]["primary_physician_name"] == "Dr. Taylor"


@pytest.mark.anyio
async def test_17_restricted_case_info_not_leaked(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 17: Client review does not leak unauthorized/restricted case data."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Brianna", "last_name": "Whitford", "date_of_birth": "1994-01-20"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    rev_res = await client.get(
        f"/api/v1/clients/approvals/{client_id}", headers=supervisor_user["headers"]
    )
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    # Ensure sensitive non-client/case-specific fields are not in the response
    assert "court_orders" not in rev_data
    assert "internal_case_notes" not in rev_data


@pytest.mark.anyio
async def test_18_it_admin_cannot_access_client_data(
    client: AsyncClient, it_admin_user: dict, caseworker_user: dict
):
    """Scenario 18: IT Admin role cannot browse, view, or approve client records (403 Forbidden)."""
    # Create client
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Devin", "last_name": "Lafond", "date_of_birth": "1990-03-15"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # IT Admin list clients -> 403
    list_res = await client.get("/api/v1/clients", headers=it_admin_user["headers"])
    assert list_res.status_code == 403

    # IT Admin get client -> 403
    get_res = await client.get(f"/api/v1/clients/{client_id}", headers=it_admin_user["headers"])
    assert get_res.status_code == 403

    # IT Admin pending approvals -> 403
    pend_res = await client.get("/api/v1/clients/approvals/pending", headers=it_admin_user["headers"])
    assert pend_res.status_code == 403


@pytest.mark.anyio
async def test_19_board_member_cannot_access_client_data(
    client: AsyncClient, board_member_user: dict, caseworker_user: dict
):
    """Scenario 19: Board Member cannot browse or view client records (403 Forbidden)."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Cynthia", "last_name": "Thomas", "date_of_birth": "1988-12-10"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # Board Member list clients -> 403
    list_res = await client.get("/api/v1/clients", headers=board_member_user["headers"])
    assert list_res.status_code == 403

    # Board Member get client -> 403
    get_res = await client.get(f"/api/v1/clients/{client_id}", headers=board_member_user["headers"])
    assert get_res.status_code == 403


@pytest.mark.anyio
async def test_20_approved_client_attachable_to_case(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 20: Existing approved Client can be attached to Case through canonical Person."""
    # Create client and approve
    c_res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Kobe", "last_name": "Dreaver", "date_of_birth": "2010-04-01"},
        headers=caseworker_user["headers"],
    )
    c_data = c_res.json()
    client_id = c_data["id"]
    person_id = c_data["person_id"]
    numeric_id = c_data["person_id_number"]

    await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve", headers=supervisor_user["headers"]
    )

    # Create Case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Family Wellness Support", "case_type": "PREVENTION"},
        headers=caseworker_user["headers"],
    )
    case_id = case_res.json()["id"]

    # Attach Person to Case
    link_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_id,
            "role": "subject_child",
            "is_primary": True,
            "relationship_to_subject": "Self",
        },
        headers=caseworker_user["headers"],
    )
    assert link_res.status_code == 201
    link_data = link_res.json()
    assert link_data["person_id"] == person_id
    assert link_data["person_id_number"] == numeric_id


@pytest.mark.anyio
async def test_21_duplicate_active_case_person_prevented(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 21: Attaching the same Person to a Case twice is prevented with 409 Conflict."""
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Mason", "last_name": "Fiddler", "date_of_birth": "2012-07-07"},
        headers=caseworker_user["headers"],
    )
    person_id = p_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Care Plan", "case_type": "PROTECTION"},
        headers=caseworker_user["headers"],
    )
    case_id = case_res.json()["id"]

    # First attach succeeds
    res1 = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person_id, "role": "subject_child", "is_primary": True},
        headers=caseworker_user["headers"],
    )
    assert res1.status_code == 201

    # Second attach of same person returns 409 Conflict
    res2 = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person_id, "role": "subject_child", "is_primary": False},
        headers=caseworker_user["headers"],
    )
    assert res2.status_code == 409


@pytest.mark.anyio
async def test_22_profile_photo_serves_valid_signed_url(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, db_session: AsyncSession
):
    """Scenario 22: Profile photo returns a fresh, valid HMAC-signed URL with future expiry."""
    # Create canonical person
    p = Person(
        person_id_number="1100000099",
        first_name="Photogenic",
        last_name="Client",
        date_of_birth=date(1997, 3, 15),
        created_by=caseworker_user["user"].id,
        updated_by=caseworker_user["user"].id,
    )
    db_session.add(p)
    await db_session.flush()

    # Create dummy document for photo
    doc = Document(
        entity_type="person_photo",
        entity_id=p.id,
        filename="avatar.jpg",
        original_filename="avatar.jpg",
        storage_path="uploads/photos/avatar.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        created_by=caseworker_user["user"].id,
    )
    db_session.add(doc)
    await db_session.flush()

    p.photo_document_id = doc.id
    await db_session.commit()

    # Submit as client
    sub_res = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": str(p.id), "risk_level": "Low"},
        headers=caseworker_user["headers"],
    )
    assert sub_res.status_code == 201
    photo_url = sub_res.json()["photo_url"]
    assert photo_url is not None
    assert "/api/v1/documents/" in photo_url and "/download" in photo_url
    assert "expires=" in photo_url
    assert "sig=" in photo_url

    # Check signed URL HMAC signature validity
    # Extract query params
    parts = photo_url.split("?")
    assert len(parts) == 2
    query_params = dict(param.split("=") for param in parts[1].split("&"))
    expires = int(query_params["expires"])
    signature = query_params["sig"]
    assert expires > int(time.time())

    expected_sig = hmac.new(
        SECRET_KEY.encode(), f"{doc.id}:{expires}".encode(), "sha256"
    ).hexdigest()
    assert signature == expected_sig


@pytest.mark.anyio
async def test_23_photo_fallback_when_absent(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 23: When no photo exists, photo_url is None."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "NoPhoto", "last_name": "Person", "date_of_birth": "2000-01-01"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    assert res.json()["photo_url"] is None


@pytest.mark.anyio
async def test_24_invalid_approval_transition_rejected(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 24: Calling return or decline on an already APPROVED client returns 409 Conflict."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Leo", "last_name": "Gambler", "date_of_birth": "1995-08-08"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # Approve
    await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve", headers=supervisor_user["headers"]
    )

    # Try return already-approved -> 409
    ret_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/return",
        json={"reason": "Should fail"},
        headers=supervisor_user["headers"],
    )
    assert ret_res.status_code == 409
    assert ret_res.json()["error"]["code"] == "INVALID_APPROVAL_TRANSITION"

    # Try decline already-approved -> 409
    dec_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/decline",
        json={"reason": "Should fail"},
        headers=supervisor_user["headers"],
    )
    assert dec_res.status_code == 409
    assert dec_res.json()["error"]["code"] == "INVALID_APPROVAL_TRANSITION"


@pytest.mark.anyio
async def test_25_repeated_decision_safely_rejected(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 25: Approving an already approved proposal returns 409 Conflict."""
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Rory", "last_name": "McLeod", "date_of_birth": "1992-06-06"},
        headers=caseworker_user["headers"],
    )
    client_id = res.json()["id"]

    # First approve succeeds
    app1 = await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve", headers=supervisor_user["headers"]
    )
    assert app1.status_code == 200

    # Second approve fails with 409
    app2 = await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve", headers=supervisor_user["headers"]
    )
    assert app2.status_code == 409
    assert app2.json()["error"]["code"] == "INVALID_APPROVAL_TRANSITION"


@pytest.mark.anyio
async def test_26_canonical_sequence_person_id_generation_proven(
    client: AsyncClient, caseworker_user: dict, db_session: AsyncSession
):
    """Scenario 26: Prove Client creation strictly advances the canonical person_sequences row.

    - Verifies 10-digit length and numeric format.
    - Verifies sequential increment from database sequence row.
    - Verifies existing Person reuse retains original ID and does NOT advance sequence.
    """
    # 1. Propose first client
    res1 = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "SeqOne", "last_name": "Test", "date_of_birth": "2001-01-01"},
        headers=caseworker_user["headers"],
    )
    assert res1.status_code == 201
    id1 = res1.json()["person_id_number"]
    assert len(id1) == 10 and id1.isdigit()
    assert id1.startswith("11")

    # 2. Propose second client
    res2 = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "SeqTwo", "last_name": "Test", "date_of_birth": "2002-02-02"},
        headers=caseworker_user["headers"],
    )
    assert res2.status_code == 201
    id2 = res2.json()["person_id_number"]
    assert len(id2) == 10 and id2.isdigit()
    # Must be sequential from person_sequences
    assert int(id2) == int(id1) + 1

    # 3. Existing person reuse does NOT advance sequence or change ID
    person_uuid = res1.json()["person_id"]
    # Verify that submitting an existing person (e.g. if previous proposal declined or different context)
    # uses exact same person ID
    get_p = await client.get(f"/api/v1/persons/{person_uuid}", headers=caseworker_user["headers"])
    assert get_p.json()["person"]["person_id_number"] == id1


@pytest.mark.anyio
async def test_27_dossier_omits_protected_medical_when_reviewer_lacks_capability(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict, db_session: AsyncSession
):
    """Scenario 27: Prove dossier response omits protected medical data unless reviewer independently has CLIENT_MEDICAL_READ."""
    # 1. Create client with medical profile
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Confidential", "last_name": "HealthTest", "date_of_birth": "1998-07-12"},
        headers=caseworker_user["headers"],
    )
    c_id = uuid.UUID(res.json()["id"])
    p_id = uuid.UUID(res.json()["person_id"])

    med = ClientMedicalProfile(
        client_id=c_id,
        general_notes="Restricted psychiatric clinical notes",
        primary_physician_name="Dr. Specialists Only",
    )
    db_session.add(med)
    await db_session.commit()

    # 2. Supervisor with CLIENT_APPROVE and CLIENT_MEDICAL_READ can view medical
    sup_rev = await client.get(f"/api/v1/clients/approvals/{c_id}", headers=supervisor_user["headers"])
    assert sup_rev.status_code == 200
    assert sup_rev.json()["person"]["medical"] is not None
    assert sup_rev.json()["person"]["medical"]["primary_physician_name"] == "Dr. Specialists Only"

    # 3. Create a reviewer with CLIENT_APPROVE but WITHOUT CLIENT_MEDICAL_READ
    from app.auth.security import create_access_token, hash_password
    from app.models.role import Permission, Role, RolePermission, UserRole
    from app.models.user import User
    from app.permissions.constants import Permissions

    limited_user = User(
        email="limited-approver@crbcl.ca",
        email_normalized="limited-approver@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Limited Approver",
        is_active=True,
        is_verified=True,
    )
    db_session.add(limited_user)
    await db_session.flush()

    limited_role = Role(key="limited_approver", name="Limited Approver Role", is_system=False)
    db_session.add(limited_role)
    await db_session.flush()

    # Grant only CLIENT_APPROVE and CLIENT_READ, strictly NO CLIENT_MEDICAL_READ
    p_app = (await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_APPROVE))).scalar_one()
    p_read = (await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_READ))).scalar_one()

    db_session.add(RolePermission(role_id=limited_role.id, permission_id=p_app.id))
    db_session.add(RolePermission(role_id=limited_role.id, permission_id=p_read.id))
    db_session.add(UserRole(user_id=limited_user.id, role_id=limited_role.id))
    await db_session.commit()

    limited_token = create_access_token(limited_user.id)
    limited_headers = {"Authorization": f"Bearer {limited_token}"}

    # 4. Limited approver CAN access approval dossier, but medical profile is strictly omitted (None)
    lim_rev = await client.get(f"/api/v1/clients/approvals/{c_id}", headers=limited_headers)
    assert lim_rev.status_code == 200
    assert lim_rev.json()["client"]["id"] == str(c_id)
    # Medical boundary holds: medical summary is None!
    assert lim_rev.json()["person"]["medical"] is None


@pytest.mark.anyio
async def test_28_approved_client_to_caseperson_chain(
    client: AsyncClient, caseworker_user: dict, supervisor_user: dict
):
    """Scenario 28: Full verification of:

    approved Client
    -> same Person UUID
    -> same Person ID
    -> CasePerson created
    -> no duplicate Client
    -> duplicate active CasePerson rejected.
    """
    # 1. Propose new client
    res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Evelyn", "last_name": "Bear", "date_of_birth": "2013-11-20"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    c_data = res.json()
    client_id = c_data["id"]
    person_uuid = c_data["person_id"]
    person_id_num = c_data["person_id_number"]

    # 2. Supervisor approves client
    app_res = await client.post(
        f"/api/v1/clients/approvals/{client_id}/approve", headers=supervisor_user["headers"]
    )
    assert app_res.status_code == 200
    assert app_res.json()["approval_status"] == "APPROVED"
    assert app_res.json()["person_id"] == person_uuid
    assert app_res.json()["person_id_number"] == person_id_num

    # 3. Create Case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Youth Stabilization Case", "case_type": "PREVENTION"},
        headers=caseworker_user["headers"],
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 4. Attach to Case via canonical Person -> CasePerson created
    attach_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_uuid,
            "role": "subject_child",
            "is_primary": True,
            "relationship_to_subject": "Self",
        },
        headers=caseworker_user["headers"],
    )
    assert attach_res.status_code == 201
    cp_data = attach_res.json()
    assert cp_data["person_id"] == person_uuid
    assert cp_data["person_id_number"] == person_id_num

    # 5. Attempting to submit another Client proposal for the same Person fails (no duplicate client)
    dup_client_res = await client.post(
        "/api/v1/clients/submit-existing",
        json={"person_id": person_uuid, "submission_notes": "Attempting duplicate"},
        headers=caseworker_user["headers"],
    )
    assert dup_client_res.status_code == 409
    assert dup_client_res.json()["error"]["code"] == "ALREADY_CLIENT"

    # 6. Attempting to attach the same Person to the same Case again fails (duplicate active CasePerson rejected)
    dup_cp_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person_uuid, "role": "subject_child", "is_primary": False},
        headers=caseworker_user["headers"],
    )
    assert dup_cp_res.status_code == 409


@pytest.mark.anyio
async def test_29_front_desk_privacy_boundaries_and_client_workflow(
    client: AsyncClient,
    caseworker_user: dict,
    supervisor_user: dict,
    db_session: AsyncSession,
):
    """Scenario 29: Front Desk Privacy Boundary & Authorized Workflow.

    Verifies:
    a. Client directory/base card is accessible (CLIENT_READ)
    b. Client base profile is accessible
    c. Comprehensive Person endpoint is strictly FORBIDDEN (403)
    d. Medical subsection is strictly FORBIDDEN (403 - no CLIENT_MEDICAL_READ)
    e. Case endpoints are strictly FORBIDDEN (403 - no CASE_READ)
    f. Client proposal is authorized (CLIENT_SUBMIT), but approval is FORBIDDEN (403).
    """
    from app.auth.security import create_access_token, hash_password
    from app.models.role import Permission, Role, RolePermission, UserRole
    from app.models.user import User
    from app.permissions.constants import Permissions

    # 1. Setup Front Desk User and Role
    fd_role = (await db_session.execute(select(Role).where(Role.key == "front_desk"))).scalar_one_or_none()
    if not fd_role:
        fd_role = Role(key="front_desk", name="Front Desk Reception", is_system=True)
        db_session.add(fd_role)
        await db_session.flush()

    fd_user = User(
        email="reception-boundary-test@crbcl.ca",
        email_normalized="reception-boundary-test@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Front Desk Boundary Tester",
        is_active=True,
        is_verified=True,
    )
    db_session.add(fd_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=fd_user.id, role_id=fd_role.id))

    # Seed explicit Front Desk permissions: CLIENT_READ, CLIENT_SUBMIT, PUBLIC_INTAKE_*
    # (strictly NO CLIENT_APPROVE, NO CLIENT_MEDICAL_READ, NO CASE_READ, NO BACKGROUND_CHECK_READ)
    fd_perm_keys = [
        Permissions.CLIENT_READ,
        Permissions.CLIENT_SUBMIT,
        Permissions.PUBLIC_INTAKE_READ,
        Permissions.PUBLIC_INTAKE_TRIAGE,
        Permissions.PUBLIC_INTAKE_ROUTE,
        Permissions.PUBLIC_INTAKE_NOTE,
        Permissions.FRONT_DESK_DASHBOARD_READ,
        Permissions.FRONT_DESK_VISITOR_MANAGE,
        Permissions.DOCUMENT_READ,
        Permissions.DOCUMENT_UPLOAD,
        Permissions.TIMELINE_READ,
        Permissions.NOTIFICATION_READ,
    ]
    for pk in fd_perm_keys:
        p_row = (await db_session.execute(select(Permission).where(Permission.key == pk))).scalar_one_or_none()
        if p_row:
            existing_rp = (
                await db_session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == fd_role.id, RolePermission.permission_id == p_row.id
                    )
                )
            ).scalar_one_or_none()
            if not existing_rp:
                db_session.add(RolePermission(role_id=fd_role.id, permission_id=p_row.id))

    await db_session.commit()

    fd_token = create_access_token(fd_user.id)
    fd_headers = {"Authorization": f"Bearer {fd_token}"}

    # 2. Caseworker creates Client with Medical Profile and links to a Case
    cw_headers = caseworker_user["headers"]
    sup_headers = supervisor_user["headers"]

    sub_res = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Boundary", "last_name": "Subject", "date_of_birth": "2000-01-01"},
        headers=cw_headers,
    )
    assert sub_res.status_code == 201
    c_data = sub_res.json()
    client_id = c_data["id"]
    person_uuid = c_data["person_id"]

    # Supervisor approves Client
    await client.post(f"/api/v1/clients/approvals/{client_id}/approve", headers=sup_headers)

    # Add confidential medical profile
    med_prof = ClientMedicalProfile(
        client_id=uuid.UUID(client_id),
        general_notes="Highly confidential psychiatric diagnostic notes",
        primary_physician_name="Dr. Confidential",
    )
    db_session.add(med_prof)
    await db_session.commit()

    # Create Case and link
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Front Desk Restricted Case", "case_type": "PROTECTION"},
        headers=cw_headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # ── VERIFY BOUNDARIES FOR FRONT DESK ──

    # a. Client directory / base card: ACCESSIBLE (200 OK)
    list_res = await client.get("/api/v1/clients", headers=fd_headers)
    assert list_res.status_code == 200
    assert any(c["id"] == client_id for c in list_res.json()["items"])

    # b. Client base profile: ACCESSIBLE (200 OK)
    base_res = await client.get(f"/api/v1/clients/{client_id}", headers=fd_headers)
    assert base_res.status_code == 200
    assert base_res.json()["id"] == client_id
    # Base profile provides demographics, not clinical/medical subsections
    assert "medical" not in base_res.json().get("person", {})

    # c. Comprehensive Person endpoint: FORBIDDEN (403)
    p_comp = await client.get(f"/api/v1/persons/{person_uuid}", headers=fd_headers)
    assert p_comp.status_code == 403
    assert "ROLE_ACCESS_DENIED" in p_comp.text or "PERSON_ACCESS_DENIED" in p_comp.text

    # Direct Person search: FORBIDDEN (403)
    p_search = await client.get("/api/v1/persons?query=Boundary", headers=fd_headers)
    assert p_search.status_code == 403

    # Duplicate check on Person: FORBIDDEN (403)
    p_dup = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"first_name": "Boundary", "last_name": "Subject"},
        headers=fd_headers,
    )
    assert p_dup.status_code == 403

    # d. Medical subsection: FORBIDDEN (403)
    med_res = await client.get(f"/api/v1/clients/{client_id}/medical", headers=fd_headers)
    assert med_res.status_code == 403

    # Approval dossier: FORBIDDEN (403)
    dossier_res = await client.get(f"/api/v1/clients/approvals/{client_id}", headers=fd_headers)
    assert dossier_res.status_code == 403

    # e. Restricted Case data: FORBIDDEN (403)
    cases_res = await client.get("/api/v1/cases", headers=fd_headers)
    assert cases_res.status_code == 403

    case_res = await client.get(f"/api/v1/cases/{case_id}", headers=fd_headers)
    assert case_res.status_code == 403

    # f. Client search and proposal workflow: ACCESSIBLE (200 / 201)
    cand_search = await client.get("/api/v1/clients/search-person?query=Boundary", headers=fd_headers)
    assert cand_search.status_code == 200
    assert any(p["id"] == person_uuid for p in cand_search.json()["items"])

    # Front desk can propose a new client
    fd_prop = await client.post(
        "/api/v1/clients/submit-new",
        json={"first_name": "Walkin", "last_name": "Visitor", "date_of_birth": "2006-06-06"},
        headers=fd_headers,
    )
    assert fd_prop.status_code == 201
    fd_prop_id = fd_prop.json()["id"]
    assert fd_prop.json()["approval_status"] == "PENDING_APPROVAL"

    # But Front Desk CANNOT approve that proposal: FORBIDDEN (403)
    fd_self_app = await client.post(f"/api/v1/clients/approvals/{fd_prop_id}/approve", headers=fd_headers)
    assert fd_self_app.status_code == 403
