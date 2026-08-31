from datetime import date
import pytest
from httpx import AsyncClient

from app.models.person import Person


@pytest.mark.anyio
async def test_case_people_and_assignments(client: AsyncClient, supervisor_user: dict, db_session):
    headers = supervisor_user["headers"]

    # 1. Create Person
    person = Person(
        first_name="Jordan",
        last_name="Crane",
        date_of_birth=date(2015, 6, 12),
        gender="Male",
    )
    db_session.add(person)
    await db_session.commit()
    person_id = str(person.id)

    # 2. Create Case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Support for Jordan Crane", "case_type": "PREVENTION", "priority": "Medium"},
        headers=headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 3. Add Person to Case Roster
    add_person_res = await client.post(
        f"/api/v1/cases/{case_id}/people",
        json={
            "person_id": person_id,
            "role": "subject_child",
            "is_primary": True,
            "relationship_to_subject": "Self",
            "notes": "Primary subject child for prevention services.",
        },
        headers=headers,
    )
    assert add_person_res.status_code == 201
    assert add_person_res.json()["role"] == "subject_child"
    assert add_person_res.json()["is_primary"] is True

    # 4. List People
    list_people_res = await client.get(f"/api/v1/cases/{case_id}/people", headers=headers)
    assert list_people_res.status_code == 200
    people = list_people_res.json()
    assert len(people) >= 1
    assert people[0]["person_first_name"] == "Jordan"

    # 5. Assign Worker
    current_user_id = str(supervisor_user["user"].id)

    assign_res = await client.post(
        f"/api/v1/cases/{case_id}/assignments",
        json={
            "user_id": current_user_id,
            "role": "primary_investigator",
            "notes": "Assigned as lead caseworker.",
        },
        headers=headers,
    )
    assert assign_res.status_code == 201
    assignment = assign_res.json()
    assert assignment["role"] == "primary_investigator"
    assert assignment["is_active"] is True

    # 6. Unassign Worker
    unassign_res = await client.delete(
        f"/api/v1/cases/{case_id}/assignments/{assignment['id']}",
        headers=headers,
    )
    assert unassign_res.status_code == 204

    # 7. Verify Historical Assignment Status
    list_assign_res = await client.get(f"/api/v1/cases/{case_id}/assignments", headers=headers)
    assert list_assign_res.status_code == 200
    assignments = list_assign_res.json()
    assert any(a["id"] == assignment["id"] and a["is_active"] is False for a in assignments)
