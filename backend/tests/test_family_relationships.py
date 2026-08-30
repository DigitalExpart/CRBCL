"""Family members, directional relationships, and genogram test suite."""

import pytest
from httpx import AsyncClient
from app.models.person import Person
from app.models.family import Family
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_family_relationships_and_genogram(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    # 1. Create family
    fam_res = await client.post(
        "/api/v1/families",
        json={"family_name": "Ahenakew Family", "status": "Active"},
        headers=caseworker_user["headers"],
    )
    assert fam_res.status_code == 201
    family_id = fam_res.json()["id"]

    # 2. Create two persons (Mother & Child)
    p_mother = Person(first_name="Mary", last_name="Ahenakew", gender="Female")
    p_child = Person(first_name="Leo", last_name="Ahenakew", gender="Male")
    db_session.add_all([p_mother, p_child])
    await db_session.commit()

    # 3. Add members to family
    await client.post(
        f"/api/v1/families/{family_id}/members",
        json={"person_id": str(p_mother.id), "role": "Mother"},
        headers=caseworker_user["headers"],
    )
    await client.post(
        f"/api/v1/families/{family_id}/members",
        json={"person_id": str(p_child.id), "role": "Child"},
        headers=caseworker_user["headers"],
    )

    # 4. Create directional relationship (Mother -> Child)
    rel_res = await client.post(
        f"/api/v1/families/{family_id}/relationships",
        json={"person_a_id": str(p_mother.id), "person_b_id": str(p_child.id), "relationship_type": "mother_of"},
        headers=caseworker_user["headers"],
    )
    assert rel_res.status_code == 201

    # 5. Fetch Genogram
    genogram_res = await client.get(f"/api/v1/families/{family_id}/genogram", headers=caseworker_user["headers"])
    assert genogram_res.status_code == 200
    genogram = genogram_res.json()
    assert len(genogram["nodes"]) >= 2
    assert len(genogram["edges"]) >= 1
    assert genogram["edges"][0]["label"] == "Mother Of"
