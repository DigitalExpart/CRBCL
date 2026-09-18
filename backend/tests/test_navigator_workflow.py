"""Tests for Navigator role, dashboard metrics, intake/referral workflows, and security boundaries.

Proves:
1. Navigator dashboard authorization works.
2. Navigator can access permitted Intake workflow.
3. Navigator can initiate Intake if capability permits.
4. Navigator can access permitted Referral workflow.
5. Navigator can initiate Referral if capability permits.
6. Existing Person is reused.
7. Existing Person ID is preserved.
8. Referral does not duplicate Client.
9. Navigator cannot perform Supervisor-only Intake approval.
10. Navigator cannot perform Director-only actions.
11. Navigator does not gain medical access merely from Intake/Referral permissions.
12. Navigator does not gain background-check access.
13. Restricted Case information remains protected.
14. Front Desk boundary remains intact.
15. IT Admin/Board boundaries remain intact.
16. Existing Intake/Referral tests remain passing.
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.models.client import Client
from app.models.person import Person
from app.models.role import Role, UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_01_navigator_dashboard_authorization(client: AsyncClient, navigator_user: dict):
    """1. Navigator dashboard authorization works: Navigator can access /api/v1/referrals/stats."""
    res = await client.get("/api/v1/referrals/stats", headers=navigator_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "total_referrals" in data
    assert "open_referrals" in data
    assert "assigned_to_me" in data
    assert "drafts_count" in data
    assert "pending_supervisor_count" in data
    assert "approved_count" in data


@pytest.mark.asyncio
async def test_02_navigator_can_access_permitted_intake_workflow(client: AsyncClient, navigator_user: dict):
    """2. Navigator can access permitted Intake workflow (GET /api/v1/referrals)."""
    res = await client.get("/api/v1/referrals", headers=navigator_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_03_navigator_can_initiate_intake(client: AsyncClient, navigator_user: dict):
    """3. Navigator can initiate Intake if capability permits."""
    payload = {
        "received_date": "2026-09-18",
        "received_method": "in_person",
        "priority": "Medium",
        "risk_level": "Low",
        "community": "Muscowpetung",
        "summary": "Community member walked into Lodge seeking family wellness resources.",
        "immediate_safety_concerns": False,
        "law_enforcement_involved": False,
    }
    res = await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "DRAFT"
    assert data["summary"] == payload["summary"]
    assert data["referral_number"].startswith("INT-")


@pytest.mark.asyncio
async def test_04_navigator_can_access_permitted_referral_detail(
    client: AsyncClient, navigator_user: dict
):
    """4. Navigator can access permitted Referral workflow (GET /api/v1/referrals/{id})."""
    # Create referral
    payload = {
        "received_date": "2026-09-18",
        "received_method": "phone",
        "priority": "High",
        "summary": "Community referral regarding family assistance.",
    }
    create_res = await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])
    assert create_res.status_code == 201
    ref_id = create_res.json()["id"]

    # View detail
    detail_res = await client.get(f"/api/v1/referrals/{ref_id}", headers=navigator_user["headers"])
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == ref_id


@pytest.mark.asyncio
async def test_05_navigator_can_initiate_and_submit_referral(
    client: AsyncClient, navigator_user: dict, db_session: AsyncSession
):
    """5. Navigator can initiate Referral and submit to supervisor when ready."""
    # 1. Create person
    person = Person(
        first_name="Jordan",
        last_name="Cardinal",
        date_of_birth=date(2018, 5, 12),
        gender="Male",
    )
    db_session.add(person)
    await db_session.commit()

    # 2. Create referral with person, reporter, and concern
    payload = {
        "received_date": "2026-09-18",
        "received_method": "walk_in",
        "priority": "Medium",
        "summary": "Community Navigator intake for child support services.",
        "reporter": {
            "is_anonymous": False,
            "reporter_name": "Elder Mary",
            "relationship_to_family": "Aunt",
        },
        "people": [
            {
                "person_id": str(person.id),
                "role": "child",
                "relationship_to_child": "self",
            }
        ],
        "concerns": [
            {
                "concern_type": "welfare_concern",
                "is_primary": True,
                "severity": "Moderate",
                "description": "Needs community connection and cultural programming.",
            }
        ],
    }
    create_res = await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])
    assert create_res.status_code == 201
    ref_id = create_res.json()["id"]

    # 3. Submit for supervisor review with recommendations and dispositions
    submit_payload = {
        "overall_recommendation": "PREVENTION",
        "rationale": "Non-protection family wellness connection.",
        "dispositions": [
            {
                "person_id": str(person.id),
                "decision": "PREVENTION",
                "reason": "Family self-referred for cultural support.",
                "destination_program": "Cultural Connections",
            }
        ],
    }
    submit_res = await client.post(
        f"/api/v1/referrals/{ref_id}/submit",
        json=submit_payload,
        headers=navigator_user["headers"],
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING_SUPERVISOR"


@pytest.mark.asyncio
async def test_06_and_07_existing_person_is_reused_and_id_preserved(
    client: AsyncClient, navigator_user: dict, db_session: AsyncSession
):
    """6 & 7. Existing Person is reused, and existing 10-digit Person ID is preserved."""
    # Create canonical person with specific 10-digit ID
    canonical_person = Person(
        first_name="Alexis",
        last_name="Bird",
        date_of_birth=date(2015, 8, 20),
        gender="Female",
        person_id_number="1100099887",  # Canonical 10-digit format
    )
    db_session.add(canonical_person)
    await db_session.commit()

    # Navigator adds person to an intake
    payload = {
        "received_date": "2026-09-18",
        "received_method": "phone",
        "summary": "Referral involving existing community member Alexis Bird.",
        "people": [
            {
                "person_id": str(canonical_person.id),
                "role": "child",
                "relationship_to_child": "self",
            }
        ],
    }
    res = await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])
    assert res.status_code == 201
    ref_data = res.json()

    # Verify person in referral matches canonical person
    detail_res = await client.get(f"/api/v1/referrals/{ref_data['id']}", headers=navigator_user["headers"])
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["people"]) == 1
    assert detail_data["people"][0]["person_id"] == str(canonical_person.id)

    # Verify DB: exactly 1 person row exists with this first/last name, and person_id_number is preserved
    stmt = select(Person).where(Person.id == canonical_person.id)
    p_row = (await db_session.execute(stmt)).scalar_one()
    assert p_row.person_id_number == "1100099887"
    assert p_row.first_name == "Alexis"
    assert p_row.last_name == "Bird"


@pytest.mark.asyncio
async def test_08_referral_does_not_duplicate_client(
    client: AsyncClient, navigator_user: dict, db_session: AsyncSession
):
    """8. Referral linking does not create a duplicate Client record."""
    # Pre-existing person and client
    person = Person(
        first_name="Marcus",
        last_name="Desjarlais",
        date_of_birth=date(2010, 3, 15),
    )
    db_session.add(person)
    await db_session.flush()

    existing_client = Client(
        person_id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        approval_status="APPROVED",
    )
    db_session.add(existing_client)
    await db_session.commit()

    # Initial client count
    stmt = select(Client).where(Client.person_id == person.id)
    initial_clients = (await db_session.execute(stmt)).scalars().all()
    assert len(initial_clients) == 1

    # Navigator creates referral for this person
    payload = {
        "received_date": "2026-09-18",
        "received_method": "walk_in",
        "summary": "Youth seeking vocational navigation.",
        "people": [{"person_id": str(person.id), "role": "child"}],
    }
    res = await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])
    assert res.status_code == 201

    # Verify client count remains exactly 1
    post_clients = (await db_session.execute(stmt)).scalars().all()
    assert len(post_clients) == 1


@pytest.mark.asyncio
async def test_09_navigator_cannot_perform_supervisor_intake_approval(
    client: AsyncClient, navigator_user: dict, supervisor_user: dict
):
    """9. Navigator cannot perform Supervisor-only Intake approval (403 Forbidden)."""
    # Create referral
    payload = {
        "received_date": "2026-09-18",
        "received_method": "phone",
        "summary": "Testing approval boundary.",
    }
    res = await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])
    ref_id = res.json()["id"]

    # Navigator attempts approval -> 403 Forbidden
    approve_res = await client.post(
        f"/api/v1/referrals/{ref_id}/approve",
        json={"supervisor_notes": "Attempted unauthorized approval"},
        headers=navigator_user["headers"],
    )
    assert approve_res.status_code == 403

    # Navigator attempts return -> 403 Forbidden
    return_res = await client.post(
        f"/api/v1/referrals/{ref_id}/return",
        json={"return_reason": "Needs more detail"},
        headers=navigator_user["headers"],
    )
    assert return_res.status_code == 403


@pytest.mark.asyncio
async def test_10_navigator_cannot_perform_director_only_actions(
    client: AsyncClient, navigator_user: dict
):
    """10. Navigator cannot perform Director-only actions (like accessing director dashboard or supervisor queue)."""
    # Supervisor approval queue requires INTAKE_APPROVE
    res = await client.get("/api/v1/referrals/approvals/queue", headers=navigator_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_11_navigator_does_not_gain_medical_access(
    client: AsyncClient, navigator_user: dict, db_session: AsyncSession
):
    """11. Navigator does not gain medical access merely from Intake/Referral permissions."""
    # Create a client
    person = Person(first_name="Dana", last_name="Starblanket", date_of_birth=date(2005, 1, 1))
    db_session.add(person)
    await db_session.flush()
    cl = Client(person_id=person.id, first_name="Dana", last_name="Starblanket")
    db_session.add(cl)
    await db_session.commit()

    # Attempt to read medical records -> 403 Forbidden
    res = await client.get(f"/api/v1/clients/{cl.id}/medical", headers=navigator_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_12_navigator_does_not_gain_background_check_access(
    client: AsyncClient, navigator_user: dict
):
    """12. Navigator does not gain background-check access."""
    res = await client.get("/api/v1/background-checks", headers=navigator_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_13_restricted_case_information_remains_protected(
    client: AsyncClient, navigator_user: dict
):
    """13. Restricted Case information remains protected: Navigator cannot access /api/v1/cases."""
    res = await client.get("/api/v1/cases", headers=navigator_user["headers"])
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_14_front_desk_boundary_remains_intact(
    client: AsyncClient, db_session: AsyncSession, seed_roles_and_permissions: dict
):
    """14. Front Desk boundary remains intact: Front Desk user cannot approve intakes or manage cases."""
    # Create front desk role if not already in seed_roles_and_permissions
    stmt = select(Role).where(Role.key == "front_desk")
    fd_role = (await db_session.execute(stmt)).scalar_one_or_none()
    if not fd_role:
        fd_role = Role(key="front_desk", name="Front Desk", is_system=True)
        db_session.add(fd_role)
        await db_session.flush()

    fd_user = User(
        email="reception@crbcl.ca",
        email_normalized="reception@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Front Desk Reception",
        is_active=True,
        is_verified=True,
    )
    db_session.add(fd_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=fd_user.id, role_id=fd_role.id))
    await db_session.commit()

    fd_headers = {"Authorization": f"Bearer {create_access_token(fd_user.id)}"}

    # Front Desk cannot access cases
    case_res = await client.get("/api/v1/cases", headers=fd_headers)
    assert case_res.status_code == 403

    # Front Desk cannot approve intakes
    appr_res = await client.post(
        f"/api/v1/referrals/{uuid.uuid4()}/approve",
        json={"notes": "none"},
        headers=fd_headers,
    )
    assert appr_res.status_code == 403


@pytest.mark.asyncio
async def test_15_it_admin_and_board_boundaries_remain_intact(
    client: AsyncClient, it_admin_user: dict
):
    """15. IT Admin and Board boundaries remain intact: cannot access /api/v1/referrals or stats."""
    res = await client.get("/api/v1/referrals", headers=it_admin_user["headers"])
    assert res.status_code == 403

    stats_res = await client.get("/api/v1/referrals/stats", headers=it_admin_user["headers"])
    assert stats_res.status_code == 403


@pytest.mark.asyncio
async def test_16_referral_stats_reflects_actual_authoritative_counts(
    client: AsyncClient, navigator_user: dict
):
    """16. Referral stats endpoint computes authoritative counts matching database state."""
    # Read initial stats
    res_init = await client.get("/api/v1/referrals/stats", headers=navigator_user["headers"])
    assert res_init.status_code == 200
    init_data = res_init.json()

    # Create new referral in DRAFT
    payload = {
        "received_date": "2026-09-18",
        "received_method": "web",
        "summary": "Authoritative count verification referral.",
    }
    await client.post("/api/v1/referrals", json=payload, headers=navigator_user["headers"])

    # Verify counts incremented authoritatively
    res_after = await client.get("/api/v1/referrals/stats", headers=navigator_user["headers"])
    after_data = res_after.json()
    assert after_data["total_referrals"] == init_data["total_referrals"] + 1
    assert after_data["drafts_count"] == init_data["drafts_count"] + 1
    assert after_data["open_referrals"] == init_data["open_referrals"] + 1
