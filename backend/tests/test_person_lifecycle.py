"""Comprehensive Person Lifecycle & Case-People Integration Tests.

Covers 20 core scenarios required for CRBCL canonical identity:
 1. Automatic numeric Person ID generation
 2. Strictly numeric 10 digits
 3. ID uniqueness and sequential increments
 4. Person ID immutability on edit
 5. Adding existing Person to Case retains same Person ID
 6. One Person in multiple Cases with same Person ID
 7. Case relationship fields remain case-specific
 8. Duplicate detection matches existing Person
 9. Duplicate flow does not auto-merge
10. Search by Person ID (exact or query)
11. New Person created and linked to Case in unified flow
12. Linked Person appears in Case People roster response with Person ID, DOB, photo
13. Full Person profile endpoint returns consolidated information
14. Unauthorized roles cannot access protected sections (medical profile gated by client.medical.read)
15. Case restrictions are respected
16. Direct IDOR / unpermitted requests rejected (403/401)
17. Board / IT Admin / unauthorized role boundaries intact
18. Physical identification fields persist and return accurately
19. Unknown optional physical fields accepted cleanly
20. Existing Person records without new optional fields remain valid
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.models.client import Client
from app.models.medical import ClientMedicalProfile
from app.models.person import (
    Person,
    PersonContact,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.person_service import PersonService


@pytest.mark.anyio
async def test_01_automatic_numeric_person_id_generation(client: AsyncClient, caseworker_user: dict):
    """Scenario 1: Person automatically receives a numeric Person ID upon creation."""
    headers = caseworker_user["headers"]
    payload = {
        "first_name": "Avery",
        "last_name": "Cardinal",
        "date_of_birth": "2014-05-18",
        "gender": "Female",
        "preferred_language": "Cree",
    }
    res = await client.post("/api/v1/persons", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "person_id_number" in data
    assert data["person_id_number"] is not None
    assert len(data["person_id_number"]) == 10


@pytest.mark.anyio
async def test_02_strictly_numeric_ten_digits(client: AsyncClient, caseworker_user: dict):
    """Scenario 2: Person ID must be strictly numeric, exactly 10 digits, no hyphens or prefixes."""
    headers = caseworker_user["headers"]
    payload = {
        "first_name": "Milo",
        "last_name": "Desjarlais",
        "date_of_birth": "2011-09-02",
        "gender": "Male",
    }
    res = await client.post("/api/v1/persons", json=payload, headers=headers)
    assert res.status_code == 201
    person_id_num = res.json()["person_id_number"]
    assert person_id_num.isdigit(), f"Expected all digits, got {person_id_num}"
    assert len(person_id_num) == 10
    assert not person_id_num.startswith("-")


@pytest.mark.anyio
async def test_03_id_uniqueness(client: AsyncClient, caseworker_user: dict):
    """Scenario 3: Consecutively created persons receive unique, sequential IDs."""
    headers = caseworker_user["headers"]
    ids = set()
    for i in range(4):
        payload = {
            "first_name": f"Sibling{i}",
            "last_name": "Ironstand",
            "date_of_birth": f"201{i}-01-01",
        }
        res = await client.post("/api/v1/persons", json=payload, headers=headers)
        assert res.status_code == 201
        p_id = res.json()["person_id_number"]
        assert p_id not in ids, f"Duplicate person_id_number generated: {p_id}"
        ids.add(p_id)
    assert len(ids) == 4


@pytest.mark.anyio
async def test_04_person_id_immutability_on_edit(client: AsyncClient, caseworker_user: dict):
    """Scenario 4: Person ID is strictly immutable; PATCH payload cannot change it."""
    headers = caseworker_user["headers"]
    # 1. Create
    res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Evelyn", "last_name": "Tanner", "date_of_birth": "2016-03-21"},
        headers=headers,
    )
    assert res.status_code == 201
    person_id = res.json()["id"]
    original_num_id = res.json()["person_id_number"]

    # 2. Attempt to tamper with person_id_number
    patch_res = await client.patch(
        f"/api/v1/persons/{person_id}",
        json={"first_name": "Evelyn-Marie", "person_id_number": "9999999999"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["first_name"] == "Evelyn-Marie"
    assert updated_data["person_id_number"] == original_num_id
    assert updated_data["person_id_number"] != "9999999999"


@pytest.mark.anyio
async def test_05_add_existing_person_to_case_retains_id(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 5: Adding existing Person to Case retains original numeric Person ID."""
    cw_headers = caseworker_user["headers"]

    # 1. Create canonical person
    person_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Toby", "last_name": "Brass", "date_of_birth": "2013-11-14"},
        headers=cw_headers,
    )
    assert person_res.status_code == 201
    person_uuid = person_res.json()["id"]
    person_num_id = person_res.json()["person_id_number"]

    # 2. Create case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Family Support - Brass", "case_type": "FAMILY_SUPPORT"},
        headers=cw_headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 3. Add Person to Case
    link_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_uuid,
            "role": "subject_child",
            "relationship_to_subject": "Self",
            "is_primary": True,
        },
        headers=cw_headers,
    )
    assert link_res.status_code == 201
    linked_data = link_res.json()
    assert linked_data["person_id"] == person_uuid
    assert linked_data["person_id_number"] == person_num_id


@pytest.mark.anyio
async def test_06_one_person_multiple_cases(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 6: One Person can be in multiple Cases with identical Person ID."""
    headers = caseworker_user["headers"]

    # 1. Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Lila", "last_name": "Sinclair", "date_of_birth": "2015-08-09"},
        headers=headers,
    )
    assert p_res.status_code == 201
    person_uuid = p_res.json()["id"]
    num_id = p_res.json()["person_id_number"]

    # 2. Create Case A and link
    case_a = (await client.post(
        "/api/v1/cases",
        json={"title": "Prevention Service A", "case_type": "PREVENTION"},
        headers=headers,
    )).json()["id"]
    await client.post(
        f"/api/v1/cases/{case_a}/people",
        json={"person_id": person_uuid, "role": "subject_child", "is_primary": True},
        headers=headers,
    )

    # 3. Create Case B and link
    case_b = (await client.post(
        "/api/v1/cases",
        json={"title": "Kinship Assessment B", "case_type": "KINSHIP"},
        headers=headers,
    )).json()["id"]
    await client.post(
        f"/api/v1/cases/{case_b}/people",
        json={"person_id": person_uuid, "role": "family_member", "is_primary": False},
        headers=headers,
    )

    # 4. Fetch Person profile and verify both cases listed
    prof_res = await client.get(f"/api/v1/persons/{person_uuid}", headers=headers)
    assert prof_res.status_code == 200
    profile = prof_res.json()
    assert profile["person"]["person_id_number"] == num_id
    linked_case_ids = [c["case_id"] for c in profile["cases"]]
    assert case_a in linked_case_ids
    assert case_b in linked_case_ids


@pytest.mark.anyio
async def test_07_case_relationship_fields_are_case_specific(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 7: Case relationship fields (role, relationship, is_primary) remain case-specific."""
    headers = caseworker_user["headers"]

    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Dakota", "last_name": "Peltier", "date_of_birth": "2008-04-12"},
        headers=headers,
    )
    person_uuid = p_res.json()["id"]

    case_1 = (await client.post(
        "/api/v1/cases", json={"title": "Case 1", "case_type": "PROTECTION"}, headers=headers
    )).json()["id"]
    case_2 = (await client.post(
        "/api/v1/cases", json={"title": "Case 2", "case_type": "FAMILY_SUPPORT"}, headers=headers
    )).json()["id"]

    # Link in Case 1 as primary subject child
    await client.post(
        f"/api/v1/cases/{case_1}/people",
        json={
            "person_id": person_uuid,
            "role": "subject_child",
            "relationship_to_subject": "Self",
            "is_primary": True,
            "notes": "Primary child in protection case",
        },
        headers=headers,
    )

    # Link in Case 2 as sibling
    await client.post(
        f"/api/v1/cases/{case_2}/people",
        json={
            "person_id": person_uuid,
            "role": "sibling",
            "relationship_to_subject": "Brother",
            "is_primary": False,
            "notes": "Sibling in family support case",
        },
        headers=headers,
    )

    # Verify roster 1
    roster_1 = (await client.get(f"/api/v1/cases/{case_1}/people", headers=headers)).json()
    cp_1 = next(p for p in roster_1 if p["person_id"] == person_uuid)
    assert cp_1["role"] == "subject_child"
    assert cp_1["is_primary"] is True
    assert cp_1["notes"] == "Primary child in protection case"

    # Verify roster 2
    roster_2 = (await client.get(f"/api/v1/cases/{case_2}/people", headers=headers)).json()
    cp_2 = next(p for p in roster_2 if p["person_id"] == person_uuid)
    assert cp_2["role"] == "sibling"
    assert cp_2["is_primary"] is False
    assert cp_2["notes"] == "Sibling in family support case"


@pytest.mark.anyio
async def test_08_duplicate_detection_matches_existing(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 8: Duplicate detection finds likely existing Person by name/DOB and numeric ID."""
    headers = caseworker_user["headers"]

    # Create reference person
    create_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Raymond",
            "last_name": "Acoose",
            "date_of_birth": "2012-07-25",
            "gender": "Male",
            "treaty_number": "TR-448291",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    person_num_id = create_res.json()["person_id_number"]

    # Duplicate check by name and DOB
    check_res = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"first_name": "Raymond", "last_name": "Acoose", "date_of_birth": "2012-07-25"},
        headers=headers,
    )
    assert check_res.status_code == 200
    res_data = check_res.json()
    assert res_data["has_potential_duplicates"] is True
    assert len(res_data["candidates"]) >= 1
    match = res_data["candidates"][0]
    assert match["person_id_number"] == person_num_id
    assert match["similarity_score"] >= 0.8

    # Duplicate check by exact Person ID number
    id_check = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"person_id_number": person_num_id},
        headers=headers,
    )
    assert id_check.status_code == 200
    assert id_check.json()["has_potential_duplicates"] is True
    assert id_check.json()["candidates"][0]["similarity_score"] >= 1.0


@pytest.mark.anyio
async def test_09_duplicate_flow_does_not_automerge(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 9: Duplicate detection alerts user but does not automatically merge or block creation."""
    headers = caseworker_user["headers"]

    # 1. Existing person
    await client.post(
        "/api/v1/persons",
        json={"first_name": "James", "last_name": "Bird", "date_of_birth": "2010-02-14"},
        headers=headers,
    )

    # 2. Check duplicate
    chk = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"first_name": "James", "last_name": "Bird", "date_of_birth": "2010-02-14"},
        headers=headers,
    )
    assert chk.json()["has_potential_duplicates"] is True

    # 3. Caseworker confirms intentional separate person (e.g. cousin with same name)
    new_p = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "James",
            "last_name": "Bird",
            "date_of_birth": "2010-02-14",
            "notes": "Verified different individual from same extended family.",
        },
        headers=headers,
    )
    assert new_p.status_code == 201
    # Both records remain distinct
    assert new_p.json()["notes"] == "Verified different individual from same extended family."


@pytest.mark.anyio
async def test_10_search_by_person_id(client: AsyncClient, caseworker_user: dict):
    """Scenario 10: Search returns exact person when queried by Person ID."""
    headers = caseworker_user["headers"]

    created = (await client.post(
        "/api/v1/persons",
        json={"first_name": "Nadine", "last_name": "Morin", "date_of_birth": "2009-10-30"},
        headers=headers,
    )).json()
    num_id = created["person_id_number"]

    # Search via person_id_number param
    res_param = await client.get(f"/api/v1/persons?person_id_number={num_id}", headers=headers)
    assert res_param.status_code == 200
    assert len(res_param.json()["items"]) == 1
    assert res_param.json()["items"][0]["person_id_number"] == num_id

    # Search via general query text
    res_query = await client.get(f"/api/v1/persons?query={num_id}", headers=headers)
    assert res_query.status_code == 200
    assert any(p["person_id_number"] == num_id for p in res_query.json()["items"])


@pytest.mark.anyio
async def test_11_new_person_created_and_linked_to_case(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 11: Unified 3-step workflow creates Person and links to Case with role."""
    headers = caseworker_user["headers"]

    # Create Case
    case_id = (await client.post(
        "/api/v1/cases", json={"title": "Child Welfare Plan", "case_type": "PROTECTION"}, headers=headers
    )).json()["id"]

    # Step 1: Search returns empty
    search = await client.get("/api/v1/persons?query=UniqueNonExistentChild", headers=headers)
    assert len(search.json()["items"]) == 0

    # Step 2: Create new Person
    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "UniqueChild",
            "last_name": "Thunderchild",
            "date_of_birth": "2017-06-20",
            "gender": "Female",
        },
        headers=headers,
    )
    assert p_res.status_code == 201
    person_data = p_res.json()

    # Step 3: Link to Case
    link_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_data["id"],
            "role": "subject_child",
            "is_primary": True,
            "relationship_to_subject": "Self",
            "notes": "Added through Add Person to Case wizard.",
        },
        headers=headers,
    )
    assert link_res.status_code == 201
    assert link_res.json()["person_id_number"] == person_data["person_id_number"]


@pytest.mark.anyio
async def test_12_linked_person_in_case_people_roster(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 12: Case People roster contains Person ID, date_of_birth, and photo_url."""
    headers = caseworker_user["headers"]

    # Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Kellan", "last_name": "Poitras", "date_of_birth": "2013-12-05"},
        headers=headers,
    )
    person = p_res.json()

    # Create Case & Link
    case_id = (await client.post(
        "/api/v1/cases", json={"title": "Roster Verification Case", "case_type": "PREVENTION"}, headers=headers
    )).json()["id"]
    await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person["id"], "role": "subject_child", "is_primary": True},
        headers=headers,
    )

    # Fetch Case People roster
    roster_res = await client.get(f"/api/v1/cases/{case_id}/people", headers=headers)
    assert roster_res.status_code == 200
    people = roster_res.json()
    assert len(people) >= 1
    target = next(p for p in people if p["person_id"] == person["id"])
    assert target["person_id_number"] == person["person_id_number"]
    assert target["date_of_birth"] == "2013-12-05"
    assert "photo_url" in target


@pytest.mark.anyio
async def test_13_full_person_profile_consolidation(
    client: AsyncClient, caseworker_user: dict, db_session: AsyncSession
):
    """Scenario 13: Full Person profile endpoint returns consolidated records across domains."""
    headers = caseworker_user["headers"]

    # 1. Create Person with physical description, address, and cultural profile
    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Serena",
            "last_name": "Bellegarde",
            "date_of_birth": "2006-04-10",
            "gender": "Female",
            "physical_description": {
                "eye_colour": "Hazel",
                "hair_colour": "Dark Brown",
                "height_cm": 162.0,
                "weight_kg": 54.0,
                "tattoos": "Star on right wrist",
                "glasses": True,
            },
            "address": {
                "address_line_1": "1420 12th Avenue",
                "city": "Regina",
                "province": "Saskatchewan",
                "postal_code": "S4P 0P3",
                "is_primary": True,
            },
            "cultural_profile": {
                "cultural_connections": "Nehiyaw / Plains Cree",
                "elders_connected": "Elder Gladys",
            },
        },
        headers=headers,
    )
    assert p_res.status_code == 201
    person_id = uuid.UUID(p_res.json()["id"])

    # 2. Add contact entry directly to test session
    contact = PersonContact(
        person_id=person_id,
        contact_type="Phone",
        value="306-555-0199",
        label="Mobile",
        is_primary=True,
    )
    db_session.add(contact)
    await db_session.commit()

    # 3. Retrieve consolidated profile
    prof_res = await client.get(f"/api/v1/persons/{person_id}", headers=headers)
    assert prof_res.status_code == 200
    data = prof_res.json()

    p_data = data["person"]
    assert p_data["first_name"] == "Serena"
    assert p_data["physical_description"]["eye_colour"] == "Hazel"
    assert p_data["physical_description"]["glasses"] is True
    assert len(p_data["addresses"]) >= 1
    assert p_data["addresses"][0]["city"] == "Regina"
    assert len(p_data["contacts"]) >= 1
    assert p_data["contacts"][0]["value"] == "306-555-0199"
    assert p_data["cultural_profile"]["elders_connected"] == "Elder Gladys"
    assert "cases" in data
    assert "referrals" in data
    assert "placements" in data
    assert "background_checks" in data
    assert "timeline" in data
    assert "documents" in data


@pytest.mark.anyio
async def test_14_unauthorized_role_cannot_access_medical(
    client: AsyncClient,
    caseworker_user: dict,
    finance_user: dict,
    db_session: AsyncSession,
    seed_roles_and_permissions: dict,
):
    """Scenario 14: Role without client.medical.read cannot view medical data in profile."""
    cw_headers = caseworker_user["headers"]
    fin_headers = finance_user["headers"]

    # 1. Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Tessa", "last_name": "McKay", "date_of_birth": "2015-02-11"},
        headers=cw_headers,
    )
    person_uuid = uuid.UUID(p_res.json()["id"])

    # 2. Link a Client and Medical Profile with finance staff as creator (operational relationship)
    c = Client(
        person_id=person_uuid,
        first_name="Tessa",
        last_name="McKay",
        date_of_birth=date(2015, 2, 11),
        status="Active",
        created_by=finance_user["user"].id,
    )
    db_session.add(c)
    await db_session.flush()

    med = ClientMedicalProfile(
        client_id=c.id,
        general_notes="Severe peanut allergy managed with EpiPen",
        dental_notes="Routine annual checkup completed",
        primary_physician_name="Dr. Sarah Campbell",
        primary_physician_phone="306-555-0144",
    )
    db_session.add(med)
    await db_session.commit()

    # 3. Caseworker (with client.medical.read) sees medical profile
    cw_res = await client.get(f"/api/v1/persons/{person_uuid}", headers=cw_headers)
    assert cw_res.status_code == 200
    assert cw_res.json()["medical"] is not None
    assert cw_res.json()["medical"]["primary_physician_name"] == "Dr. Sarah Campbell"
    assert cw_res.json()["medical"]["general_notes"] == "Severe peanut allergy managed with EpiPen"

    # 4. Finance user (lacks client.medical.read) sees medical as None
    fin_res = await client.get(f"/api/v1/persons/{person_uuid}", headers=fin_headers)
    assert fin_res.status_code == 200
    assert fin_res.json()["medical"] is None


@pytest.mark.anyio
async def test_15_case_restrictions_respected(
    client: AsyncClient, supervisor_user: dict, caseworker_user: dict
):
    """Scenario 15: Case restrictions block restricted worker from accessing case details."""
    admin_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]
    cw_user_id = str(caseworker_user["user"].id)

    # 1. Create Case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Confidential Kinship Review", "case_type": "KINSHIP"},
        headers=admin_headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Add restriction against caseworker
    restrict_res = await client.post(
        f"/api/v1/cases/{case_id}/restrictions",
        json={
            "user_id": cw_user_id,
            "restriction_type": "conflict_of_interest",
            "reason": "Caseworker is first-degree relative to caregiver.",
        },
        headers=admin_headers,
    )
    assert restrict_res.status_code == 201

    # 3. Restricted worker receives 403 Forbidden
    access_res = await client.get(f"/api/v1/cases/{case_id}", headers=cw_headers)
    assert access_res.status_code == 403
    assert "Active conflict-of-interest restriction" in access_res.text


@pytest.mark.anyio
async def test_16_direct_idor_rejected_without_permission(
    client: AsyncClient, it_admin_user: dict, caseworker_user: dict
):
    """Scenario 16: Direct-ID/IDOR requests without proper permissions return 403 Forbidden or 401."""
    cw_headers = caseworker_user["headers"]
    it_headers = it_admin_user["headers"]

    # Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Jordan", "last_name": "Favel", "date_of_birth": "2012-01-15"},
        headers=cw_headers,
    )
    person_id = p_res.json()["id"]

    # IT Admin has NO client.read permission -> 403 Forbidden
    it_res = await client.get(f"/api/v1/persons/{person_id}", headers=it_headers)
    assert it_res.status_code == 403

    # Unauthenticated -> 401 Unauthorized
    anon_res = await client.get(f"/api/v1/persons/{person_id}")
    assert anon_res.status_code in (401, 403)


@pytest.mark.anyio
async def test_17_board_front_desk_boundaries_intact(
    client: AsyncClient, it_admin_user: dict, caseworker_user: dict
):
    """Scenario 17: Administrative/system-only roles cannot mutate person records."""
    it_headers = it_admin_user["headers"]
    cw_headers = caseworker_user["headers"]

    # Create Person via authorized caseworker
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Brooke", "last_name": "Guthrie", "date_of_birth": "2013-08-20"},
        headers=cw_headers,
    )
    person_id = p_res.json()["id"]

    # IT admin cannot create person
    create_denied = await client.post(
        "/api/v1/persons",
        json={"first_name": "Illegal", "last_name": "Creation"},
        headers=it_headers,
    )
    assert create_denied.status_code == 403

    # IT admin cannot update person
    update_denied = await client.patch(
        f"/api/v1/persons/{person_id}",
        json={"first_name": "Tampered"},
        headers=it_headers,
    )
    assert update_denied.status_code == 403


@pytest.mark.anyio
async def test_18_physical_identification_fields_persist(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 18: Physical identification fields persist and return accurately."""
    headers = caseworker_user["headers"]

    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Zack",
            "last_name": "Bear",
            "date_of_birth": "2007-12-14",
            "physical_description": {
                "eye_colour": "Dark Brown",
                "hair_colour": "Black",
                "height_cm": 172.5,
                "weight_kg": 68.0,
                "tattoos": "Eagle feather on left forearm",
                "scars": "1-inch scar above left eyebrow",
                "birthmarks": "Small birthmark on shoulder",
                "piercings": "Single left earlobe piercing",
                "distinguishing_marks": "Silver wire glasses",
                "glasses": True,
                "contact_lenses": False,
                "notes": "Observable distinguishing marks verified during intake.",
            },
        },
        headers=headers,
    )
    assert p_res.status_code == 201
    person_id = p_res.json()["id"]

    # Retrieve profile
    prof = (await client.get(f"/api/v1/persons/{person_id}", headers=headers)).json()
    phys = prof["person"]["physical_description"]
    assert phys is not None
    assert phys["eye_colour"] == "Dark Brown"
    assert phys["hair_colour"] == "Black"
    assert phys["height_cm"] == 172.5
    assert phys["weight_kg"] == 68.0
    assert phys["tattoos"] == "Eagle feather on left forearm"
    assert phys["scars"] == "1-inch scar above left eyebrow"
    assert phys["birthmarks"] == "Small birthmark on shoulder"
    assert phys["piercings"] == "Single left earlobe piercing"
    assert phys["distinguishing_marks"] == "Silver wire glasses"
    assert phys["glasses"] is True


@pytest.mark.anyio
async def test_19_unknown_optional_physical_fields_accepted(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 19: Unknown/unspecified optional physical fields are accepted cleanly."""
    headers = caseworker_user["headers"]

    # Physical description with only eye_colour and height
    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Aria",
            "last_name": "Lavallee",
            "date_of_birth": "2016-09-04",
            "physical_description": {
                "eye_colour": "Brown",
                "height_cm": 120.0,
            },
        },
        headers=headers,
    )
    assert p_res.status_code == 201
    person_id = p_res.json()["id"]

    prof = (await client.get(f"/api/v1/persons/{person_id}", headers=headers)).json()
    phys = prof["person"]["physical_description"]
    assert phys["eye_colour"] == "Brown"
    assert phys["tattoos"] is None
    assert phys["scars"] is None
    assert phys["distinguishing_marks"] is None


@pytest.mark.anyio
async def test_20_existing_person_without_optional_fields_valid(
    client: AsyncClient, caseworker_user: dict, db_session: AsyncSession
):
    """Scenario 20: Existing Person records without physical/cultural profiles remain completely valid."""
    headers = caseworker_user["headers"]

    # Insert a bare legacy person directly into the DB with authorized creator
    bare_person = Person(
        first_name="Legacy",
        last_name="Record",
        date_of_birth=date(2010, 5, 20),
        gender="Unknown",
        created_by=caseworker_user["user"].id,
    )
    db_session.add(bare_person)
    await db_session.commit()

    # Query full profile via API
    res = await client.get(f"/api/v1/persons/{bare_person.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    p_data = data["person"]
    assert p_data["first_name"] == "Legacy"
    assert p_data["physical_description"] is None
    assert p_data["cultural_profile"] is None
    assert p_data["addresses"] == []
    assert p_data["contacts"] == []
    assert data["cases"] == []
    assert data["medical"] is None


@pytest.mark.anyio
async def test_21_case_roster_active_duplication_prevented(
    client: AsyncClient, caseworker_user: dict
):
    """Scenario 21: Case roster prevents duplicate active links of the same Person to the same Case."""
    headers = caseworker_user["headers"]

    # 1. Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Roster", "last_name": "DuplicateTest", "date_of_birth": "2015-01-01"},
        headers=headers,
    )
    person_id = p_res.json()["id"]

    # 2. Create Case
    c_res = await client.post(
        "/api/v1/cases",
        json={"title": "Roster Duplicate Protection", "case_type": "PREVENTION"},
        headers=headers,
    )
    case_id = c_res.json()["id"]

    # 3. Add person to case
    link_1 = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person_id, "role": "subject_child", "is_primary": True},
        headers=headers,
    )
    assert link_1.status_code == 201

    # 4. Attempt to add the exact same person to the exact same case actively again -> 409 Conflict
    link_2 = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person_id, "role": "sibling", "is_primary": False},
        headers=headers,
    )
    assert link_2.status_code == 409
    assert "already an active member of this case roster" in link_2.text


@pytest.mark.anyio
async def test_22_photo_mime_and_security_validation(
    client: AsyncClient, caseworker_user: dict, db_session: AsyncSession
):
    """Scenario 22: Profile photo upload rejects invalid MIME types and accepts valid image files."""
    headers = caseworker_user["headers"]

    # Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Photo", "last_name": "SecurityTest", "date_of_birth": "2014-03-03"},
        headers=headers,
    )
    person_id = p_res.json()["id"]

    # 1. Attempt upload with text/plain -> 400 Bad Request
    bad_upload = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("malicious.txt", b"not-an-image-content", "text/plain")},
        headers=headers,
    )
    assert bad_upload.status_code == 400

    # 2. Valid PNG image upload -> 200 OK with signed URL
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    good_upload = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("avatar.png", png_bytes, "image/png")},
        headers=headers,
    )
    assert good_upload.status_code == 200
    res = good_upload.json()
    assert "photo_url" in res
    assert "/api/v1/documents/" in res["photo_url"]
    assert "sig=" in res["photo_url"]

    # Verify durable database storage: photo_document_id is stored, photo_url is not persisted as expiring URL
    p_row = (await db_session.execute(select(Person).where(Person.id == uuid.UUID(person_id)))).scalar_one()
    assert p_row.photo_document_id is not None
    assert p_row.photo_url is None


@pytest.mark.anyio
async def test_23_idor_restricted_case_person_forbidden(
    client: AsyncClient, supervisor_user: dict, caseworker_user: dict
):
    """Scenario 23: Caseworker restricted from person's only case cannot access profile via direct IDOR."""
    admin_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]
    cw_user_id = str(caseworker_user["user"].id)

    # 1. Create Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Conflict", "last_name": "Relative", "date_of_birth": "2016-07-07"},
        headers=admin_headers,
    )
    person_id = p_res.json()["id"]

    # 2. Create Case and link Person
    c_res = await client.post(
        "/api/v1/cases",
        json={"title": "High Conflict Case", "case_type": "PROTECTION"},
        headers=admin_headers,
    )
    case_id = c_res.json()["id"]
    await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={"person_id": person_id, "role": "subject_child", "is_primary": True},
        headers=admin_headers,
    )

    # 3. Restrict Caseworker from this Case
    await client.post(
        f"/api/v1/cases/{case_id}/restrictions",
        json={
            "user_id": cw_user_id,
            "restriction_type": "conflict_of_interest",
            "reason": "Caseworker is related to this individual.",
        },
        headers=admin_headers,
    )

    # 4. Direct IDOR attempt by restricted caseworker to view Person profile -> 403 Forbidden
    idor_res = await client.get(f"/api/v1/persons/{person_id}", headers=cw_headers)
    assert idor_res.status_code == 403
    assert "active conflict-of-interest restriction" in idor_res.text.lower()

    # 5. Direct IDOR attempt by restricted caseworker to modify Person -> 403 Forbidden
    patch_res = await client.patch(
        f"/api/v1/persons/{person_id}",
        json={"notes": "Restricted update attempt"},
        headers=cw_headers,
    )
    assert patch_res.status_code == 403
    assert "active conflict-of-interest restriction" in patch_res.text.lower()

    # 6. Direct IDOR attempt by restricted caseworker to upload photo -> 403 Forbidden
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    photo_res = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("photo.png", png_bytes, "image/png")},
        headers=cw_headers,
    )
    assert photo_res.status_code == 403
    assert "active conflict-of-interest restriction" in photo_res.text.lower()


@pytest.mark.anyio
async def test_24_direct_idor_unrelated_person_denied(
    client: AsyncClient, supervisor_user: dict, caseworker_user: dict
):
    """Scenario 24: Caseworker cannot GET, PATCH, or upload photo for an unrelated Person (IDOR blocked)."""
    sup_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]

    # 1. Supervisor creates an unrelated Person (not linked to any case caseworker has access to)
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Unrelated", "last_name": "Stranger", "date_of_birth": "2008-08-08"},
        headers=sup_headers,
    )
    assert p_res.status_code == 201
    person_id = p_res.json()["id"]

    # 2. Caseworker tries to GET unrelated Person profile -> 403 PERSON_ACCESS_DENIED
    get_res = await client.get(f"/api/v1/persons/{person_id}", headers=cw_headers)
    assert get_res.status_code == 403
    assert "PERSON_ACCESS_DENIED" in get_res.text

    # 3. Caseworker tries to PATCH unrelated Person -> 403 PERSON_ACCESS_DENIED
    patch_res = await client.patch(
        f"/api/v1/persons/{person_id}",
        json={"notes": "Malicious edit attempt"},
        headers=cw_headers,
    )
    assert patch_res.status_code == 403
    assert "PERSON_ACCESS_DENIED" in patch_res.text

    # 4. Caseworker tries to upload photo for unrelated Person -> 403 PERSON_ACCESS_DENIED
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    photo_res = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("photo.png", png_bytes, "image/png")},
        headers=cw_headers,
    )
    assert photo_res.status_code == 403
    assert "PERSON_ACCESS_DENIED" in photo_res.text


@pytest.mark.anyio
async def test_25_mixed_restricted_and_accessible_cases(
    client: AsyncClient, supervisor_user: dict, caseworker_user: dict
):
    """
    Scenario 25: Person occurs on both a restricted Case AND a legitimate accessible Case.
    Base profile is accessible, but data belonging specifically to the restricted Case is excluded.
    """
    sup_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]
    cw_user_id = str(caseworker_user["user"].id)

    # 1. Supervisor creates canonical Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Mixed", "last_name": "AccessPerson", "date_of_birth": "2012-04-15"},
        headers=sup_headers,
    )
    person_id = p_res.json()["id"]

    # 2. Supervisor creates Case 1 (Protection) and links Person
    c1_res = await client.post(
        "/api/v1/cases",
        json={"title": "Restricted Protection Case", "case_type": "PROTECTION"},
        headers=sup_headers,
    )
    case_1_id = c1_res.json()["id"]
    await client.post(
        f"/api/v1/cases/{case_1_id}/people",
        json={"person_id": person_id, "role": "subject_child", "is_primary": True},
        headers=sup_headers,
    )

    # Restrict caseworker from Case 1
    await client.post(
        f"/api/v1/cases/{case_1_id}/restrictions",
        json={
            "user_id": cw_user_id,
            "restriction_type": "conflict_of_interest",
            "reason": "Caseworker family connection.",
        },
        headers=sup_headers,
    )

    # 3. Caseworker creates Case 2 (Prevention) and links Person
    c2_res = await client.post(
        "/api/v1/cases",
        json={"title": "Accessible Prevention Case", "case_type": "PREVENTION"},
        headers=cw_headers,
    )
    case_2_id = c2_res.json()["id"]
    await client.post(
        f"/api/v1/cases/{case_2_id}/people",
        json={"person_id": person_id, "role": "subject_child", "is_primary": True},
        headers=cw_headers,
    )

    # 4. Caseworker fetches Person profile -> 200 OK via Case 2 legitimate relationship
    prof_res = await client.get(f"/api/v1/persons/{person_id}", headers=cw_headers)
    assert prof_res.status_code == 200
    data = prof_res.json()
    assert data["person"]["first_name"] == "Mixed"

    # Restricted Case 1 must NOT appear in cases list; only accessible Case 2 appears
    case_ids = [c["case_id"] for c in data["cases"]]
    assert case_2_id in case_ids
    assert case_1_id not in case_ids


@pytest.mark.anyio
async def test_26_search_and_duplicate_disclosure_limited(
    client: AsyncClient, supervisor_user: dict, caseworker_user: dict
):
    """
    Scenario 26: Search and duplicate-check return minimum necessary matching fields.
    Does NOT expose address history, health info, physical identifiers, notes, or raw identifiers.
    """
    sup_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]

    # 1. Supervisor creates Person with sensitive data
    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Private",
            "last_name": "IdentityTest",
            "date_of_birth": "2005-09-09",
            "treaty_number": "TR-99887766",
            "health_card_number": "HC-11223344",
            "notes": "Highly sensitive clinical narrative.",
            "physical_description": {
                "eye_colour": "Brown",
                "hair_colour": "Black",
                "scars": "Facial scar",
                "tattoos": "Dragon tattoo",
            },
            "address": {
                "address_line_1": "99 Secret Lane",
                "city": "Saskatoon",
                "province": "SK",
                "postal_code": "S7K 1A1",
            },
        },
        headers=sup_headers,
    )
    assert p_res.status_code == 201
    person_num_id = p_res.json()["person_id_number"]

    # 2. Caseworker searches via GET /api/v1/persons?query=...
    search_res = await client.get(f"/api/v1/persons?query={person_num_id}", headers=cw_headers)
    assert search_res.status_code == 200
    items = search_res.json()["items"]
    assert len(items) == 1
    item = items[0]

    # Allowed limited fields
    assert item["person_id_number"] == person_num_id
    assert item["first_name"] == "Private"
    assert item["last_name"] == "IdentityTest"
    assert item["date_of_birth"] == "2005-09-09"

    # Disallowed sensitive fields must NOT be present in search item schema
    for sensitive_field in [
        "photo_url",
        "physical_description",
        "addresses",
        "contacts",
        "notes",
        "treaty_number",
        "health_card_number",
    ]:
        assert sensitive_field not in item

    # 3. Caseworker runs POST /api/v1/persons/duplicate-check
    dup_res = await client.post(
        "/api/v1/persons/duplicate-check",
        json={
            "first_name": "Private",
            "last_name": "IdentityTest",
            "date_of_birth": "2005-09-09",
        },
        headers=cw_headers,
    )
    assert dup_res.status_code == 200
    candidates = dup_res.json()["candidates"]
    assert len(candidates) >= 1
    candidate = next(c for c in candidates if c["person_id_number"] == person_num_id)

    # Candidate allowed matching fields
    assert candidate["similarity_score"] > 0
    assert "matching_factors" in candidate

    # Disallowed raw sensitive fields must NOT be in candidate schema
    for sensitive_field in [
        "treaty_number",
        "health_card_number",
        "phone",
        "addresses",
        "contacts",
        "notes",
        "physical_description",
    ]:
        assert sensitive_field not in candidate


@pytest.mark.anyio
async def test_27_role_boundaries_front_desk_board_it_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    it_admin_user: dict,
    caseworker_user: dict,
    seed_roles_and_permissions: dict,
):
    """
    Scenario 27: Front Desk, Board Member, and IT Admin roles are strictly barred from
    searching Person directory, duplicate checking, and reading canonical profiles.
    """
    # Create an accessible person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "Protected", "last_name": "Subject", "date_of_birth": "2011-01-01"},
        headers=caseworker_user["headers"],
    )
    person_id = p_res.json()["id"]

    # 1. IT Admin attempts
    it_headers = it_admin_user["headers"]
    it_search = await client.get("/api/v1/persons?query=Protected", headers=it_headers)
    assert it_search.status_code == 403
    it_prof = await client.get(f"/api/v1/persons/{person_id}", headers=it_headers)
    assert it_prof.status_code == 403
    it_dup = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"first_name": "Protected", "last_name": "Subject"},
        headers=it_headers,
    )
    assert it_dup.status_code == 403

    # 2. Create Front Desk Role and User
    fd_role = Role(key="front_desk", name="Front Desk Reception", is_system=True)
    db_session.add(fd_role)
    await db_session.flush()

    fd_user = User(
        email="reception@crbcl.ca",
        email_normalized="reception@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Front Desk Receptionist",
        is_active=True,
        is_verified=True,
    )
    db_session.add(fd_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=fd_user.id, role_id=fd_role.id))
    # Give front_desk CLIENT_READ to verify explicit role barrier holds even if granted permission
    p_client_read = (
        await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_READ))
    ).scalar_one()
    db_session.add(RolePermission(role_id=fd_role.id, permission_id=p_client_read.id))
    await db_session.commit()

    fd_token = create_access_token(fd_user.id)
    fd_headers = {"Authorization": f"Bearer {fd_token}"}

    fd_search = await client.get("/api/v1/persons?query=Protected", headers=fd_headers)
    assert fd_search.status_code == 403
    assert "ROLE_ACCESS_DENIED" in fd_search.text or "front desk" in fd_search.text.lower()

    fd_prof = await client.get(f"/api/v1/persons/{person_id}", headers=fd_headers)
    assert fd_prof.status_code == 403

    fd_dup = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"first_name": "Protected", "last_name": "Subject"},
        headers=fd_headers,
    )
    assert fd_dup.status_code == 403

    # 3. Create Board Member Role and User
    bm_role = Role(key="board_member", name="Board Member", is_system=True)
    db_session.add(bm_role)
    await db_session.flush()

    bm_user = User(
        email="board@crbcl.ca",
        email_normalized="board@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Governor Board",
        is_active=True,
        is_verified=True,
    )
    db_session.add(bm_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=bm_user.id, role_id=bm_role.id))
    db_session.add(RolePermission(role_id=bm_role.id, permission_id=p_client_read.id))
    await db_session.commit()

    bm_token = create_access_token(bm_user.id)
    bm_headers = {"Authorization": f"Bearer {bm_token}"}

    bm_search = await client.get("/api/v1/persons?query=Protected", headers=bm_headers)
    assert bm_search.status_code == 403
    assert "ROLE_ACCESS_DENIED" in bm_search.text or "board members" in bm_search.text.lower()

    bm_prof = await client.get(f"/api/v1/persons/{person_id}", headers=bm_headers)
    assert bm_prof.status_code == 403

    bm_dup = await client.post(
        "/api/v1/persons/duplicate-check",
        json={"first_name": "Protected", "last_name": "Subject"},
        headers=bm_headers,
    )
    assert bm_dup.status_code == 403


@pytest.mark.anyio
async def test_28_authorized_search_and_link_workflow(
    client: AsyncClient, supervisor_user: dict, caseworker_user: dict
):
    """
    Scenario 28: Full authorized Add Person workflow:
    1. Search before create returns limited candidate.
    2. Before linking, caseworker cannot directly access profile (IDOR blocked).
    3. Caseworker links person to accessible Case.
    4. After linking, caseworker has legitimate operational access to the full profile.
    """
    sup_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]

    # 1. Supervisor creates canonical Person (unrelated to caseworker)
    p_res = await client.post(
        "/api/v1/persons",
        json={
            "first_name": "Eli",
            "last_name": "Desjarlais",
            "date_of_birth": "2014-07-22",
            "gender": "Male",
        },
        headers=sup_headers,
    )
    assert p_res.status_code == 201
    person_data = p_res.json()
    person_id = person_data["id"]
    person_num_id = person_data["person_id_number"]

    # 2. Caseworker creates an accessible Case
    c_res = await client.post(
        "/api/v1/cases",
        json={"title": "Kinship Placement Case", "case_type": "PROTECTION"},
        headers=cw_headers,
    )
    case_id = c_res.json()["id"]

    # 3. Caseworker searches before create: finds candidate with limited info
    search_res = await client.get(f"/api/v1/persons?query={person_num_id}", headers=cw_headers)
    assert search_res.status_code == 200
    items = search_res.json()["items"]
    assert len(items) == 1
    assert items[0]["person_id_number"] == person_num_id

    # 4. Before linking, direct profile access is blocked (403 PERSON_ACCESS_DENIED)
    pre_link_prof = await client.get(f"/api/v1/persons/{person_id}", headers=cw_headers)
    assert pre_link_prof.status_code == 403
    assert "PERSON_ACCESS_DENIED" in pre_link_prof.text

    # 5. Caseworker links existing Person to the accessible Case
    link_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_id,
            "role": "subject_child",
            "is_primary": True,
            "relationship_to_subject": "Self",
        },
        headers=cw_headers,
    )
    assert link_res.status_code == 201
    assert link_res.json()["person_id_number"] == person_num_id

    # 6. Post-linking: Caseworker now has legitimate operational relationship!
    post_link_prof = await client.get(f"/api/v1/persons/{person_id}", headers=cw_headers)
    assert post_link_prof.status_code == 200
    data = post_link_prof.json()
    assert data["person"]["id"] == person_id
    assert data["person"]["first_name"] == "Eli"
    assert any(c["case_id"] == case_id for c in data["cases"])


@pytest.mark.anyio
async def test_29_is_system_and_admin_email_without_role_denied(
    client: AsyncClient,
    db_session: AsyncSession,
    supervisor_user: dict,
    seed_roles_and_permissions: dict,
):
    """
    Scenario 29: Regression test proving technical bypass removal:
    - is_system=True alone does NOT grant Person access.
    - email == 'admin@crbcl.ca' alone does NOT grant Person access.
    - IT Admin role remains denied.
    """
    # 1. Supervisor creates an unrelated Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "ProtectedPerson", "last_name": "NoBypass", "date_of_birth": "2010-05-12"},
        headers=supervisor_user["headers"],
    )
    assert p_res.status_code == 201
    person_id = p_res.json()["id"]

    # Retrieve CLIENT_READ permission
    p_client_read = (
        await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_READ))
    ).scalar_one()

    # 2. User with is_system=True alone (no executive or caseworker operational access)
    sys_role = Role(key="system_role", name="System Service", is_system=True)
    db_session.add(sys_role)
    await db_session.flush()
    db_session.add(RolePermission(role_id=sys_role.id, permission_id=p_client_read.id))

    sys_user = User(
        email="backend_system_job@crbcl.ca",
        email_normalized="backend_system_job@crbcl.ca",
        password_hash=hash_password("secret123"),
        full_name="System Background Worker",
        is_active=True,
        is_verified=True,
    )
    db_session.add(sys_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=sys_user.id, role_id=sys_role.id))
    await db_session.commit()

    # Verify is_system=True alone does not bypass operational access
    sys_user.is_system = True
    p_service = PersonService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await p_service.check_person_operational_access(uuid.UUID(person_id), sys_user)
    assert exc_info.value.status_code == 403

    sys_token = create_access_token(sys_user.id)
    sys_headers = {"Authorization": f"Bearer {sys_token}"}

    sys_res = await client.get(f"/api/v1/persons/{person_id}", headers=sys_headers)
    assert sys_res.status_code == 403
    assert "PERSON_ACCESS_DENIED" in sys_res.text

    # 3. User with email == 'admin@crbcl.ca' (no executive role or case operational access)
    admin_email_user = User(
        email="admin@crbcl.ca",
        email_normalized="admin@crbcl.ca",
        password_hash=hash_password("secret123"),
        full_name="Admin Email User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin_email_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=admin_email_user.id, role_id=sys_role.id))
    await db_session.commit()

    admin_email_token = create_access_token(admin_email_user.id)
    admin_email_headers = {"Authorization": f"Bearer {admin_email_token}"}

    admin_email_res = await client.get(f"/api/v1/persons/{person_id}", headers=admin_email_headers)
    assert admin_email_res.status_code == 403
    assert "PERSON_ACCESS_DENIED" in admin_email_res.text


@pytest.mark.anyio
async def test_30_executive_director_and_ceo_agency_wide_access(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    executive_director_user: dict,
    seed_roles_and_permissions: dict,
):
    """
    Scenario 30: Executive Leadership (Executive Director and CEO) retain approved
    agency-wide Person oversight across all records without requiring case assignments.
    """
    # 1. Caseworker creates a Person (unrelated to ED/CEO)
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "AgencyWide", "last_name": "Subject", "date_of_birth": "2008-01-15"},
        headers=caseworker_user["headers"],
    )
    assert p_res.status_code == 201
    person_id = p_res.json()["id"]

    # 2. Executive Director accesses the Person directly -> 200 OK
    ed_res = await client.get(f"/api/v1/persons/{person_id}", headers=executive_director_user["headers"])
    assert ed_res.status_code == 200
    assert ed_res.json()["person"]["first_name"] == "AgencyWide"

    # 3. Create CEO user and verify CEO access -> 200 OK
    ceo_role = Role(key="ceo", name="Chief Executive Officer", is_system=True)
    db_session.add(ceo_role)
    await db_session.flush()

    p_client_read = (
        await db_session.execute(select(Permission).where(Permission.key == Permissions.CLIENT_READ))
    ).scalar_one()
    db_session.add(RolePermission(role_id=ceo_role.id, permission_id=p_client_read.id))

    ceo_user = User(
        email="ceo@crbcl.ca",
        email_normalized="ceo@crbcl.ca",
        password_hash=hash_password("secret123"),
        full_name="Chief Executive Officer",
        is_active=True,
        is_verified=True,
    )
    db_session.add(ceo_user)
    await db_session.flush()
    db_session.add(UserRole(user_id=ceo_user.id, role_id=ceo_role.id))
    await db_session.commit()

    ceo_token = create_access_token(ceo_user.id)
    ceo_headers = {"Authorization": f"Bearer {ceo_token}"}

    ceo_res = await client.get(f"/api/v1/persons/{person_id}", headers=ceo_headers)
    assert ceo_res.status_code == 200
    assert ceo_res.json()["person"]["first_name"] == "AgencyWide"


@pytest.mark.anyio
async def test_31_profile_photo_storage_disclosure_and_case_roster(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    supervisor_user: dict,
    it_admin_user: dict,
):
    """
    Scenario 31: Comprehensive Profile Photo Security:
    - Search before create does NOT expose photo URL.
    - Authorized profile receives dynamic, short-lived signed URL.
    - Authorized Case People roster receives dynamic signed avatar URL.
    - Unrelated worker cannot retrieve profile or upload photo.
    - IT Admin cannot retrieve profile or upload photo.
    - Database stores durable photo_document_id and does NOT persist expiring signed URL.
    """
    cw_headers = caseworker_user["headers"]
    unrelated_headers = supervisor_user["headers"]
    it_headers = it_admin_user["headers"]

    # 1. Caseworker creates Person
    p_res = await client.post(
        "/api/v1/persons",
        json={"first_name": "PhotoSubject", "last_name": "SecureAvatar", "date_of_birth": "2013-11-20"},
        headers=cw_headers,
    )
    assert p_res.status_code == 201
    person_data = p_res.json()
    person_id = person_data["id"]
    person_num_id = person_data["person_id_number"]

    # 2. Upload photo
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    upload_res = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("profile.png", png_bytes, "image/png")},
        headers=cw_headers,
    )
    assert upload_res.status_code == 200
    upload_url = upload_res.json()["photo_url"]
    assert "/api/v1/documents/" in upload_url
    assert "sig=" in upload_url

    # 3. Check DB storage: photo_document_id set, photo_url is NULL in database
    p_db = (await db_session.execute(select(Person).where(Person.id == uuid.UUID(person_id)))).scalar_one()
    assert p_db.photo_document_id is not None
    assert p_db.photo_url is None

    # 4. Search before create: PersonSearchResultResponse must NOT disclose photo_url
    search_res = await client.get(f"/api/v1/persons?query={person_num_id}", headers=unrelated_headers)
    assert search_res.status_code == 200
    search_item = search_res.json()["items"][0]
    assert "photo_url" not in search_item

    # 5. Unrelated caseworker cannot view profile (thus cannot get signed photo URL)
    unrelated_prof = await client.get(f"/api/v1/persons/{person_id}", headers=unrelated_headers)
    assert unrelated_prof.status_code == 403

    # Unrelated caseworker cannot upload photo to this Person
    unrelated_upload = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("hacked.png", png_bytes, "image/png")},
        headers=unrelated_headers,
    )
    assert unrelated_upload.status_code == 403

    # 6. IT Admin cannot view profile or upload photo
    it_prof = await client.get(f"/api/v1/persons/{person_id}", headers=it_headers)
    assert it_prof.status_code == 403

    it_upload = await client.post(
        f"/api/v1/persons/{person_id}/photo",
        files={"file": ("it_avatar.png", png_bytes, "image/png")},
        headers=it_headers,
    )
    assert it_upload.status_code == 403

    # 7. Authorized profile receives dynamically generated signed photo URL
    auth_prof = await client.get(f"/api/v1/persons/{person_id}", headers=cw_headers)
    assert auth_prof.status_code == 200
    prof_photo = auth_prof.json()["person"]["photo_url"]
    assert prof_photo is not None
    assert "/api/v1/documents/" in prof_photo
    assert "sig=" in prof_photo

    # 8. Link Person to Case and check Case People roster returns dynamically generated signed avatar
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Photo Verification Case", "case_type": "PROTECTION"},
        headers=cw_headers,
    )
    case_id = case_res.json()["id"]

    add_p_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_id,
            "role": "subject_child",
            "is_primary": True,
            "relationship_to_subject": "Self",
        },
        headers=cw_headers,
    )
    assert add_p_res.status_code == 201
    assert add_p_res.json()["photo_url"] is not None
    assert "/api/v1/documents/" in add_p_res.json()["photo_url"]
    assert "sig=" in add_p_res.json()["photo_url"]

    roster_res = await client.get(f"/api/v1/cases/{case_id}/people", headers=cw_headers)
    assert roster_res.status_code == 200
    roster_people = roster_res.json()
    assert len(roster_people) == 1
    assert roster_people[0]["photo_url"] is not None
    assert "/api/v1/documents/" in roster_people[0]["photo_url"]
    assert "sig=" in roster_people[0]["photo_url"]
