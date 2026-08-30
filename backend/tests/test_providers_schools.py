"""Providers pool and school directory test suite."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_provider_pool_and_school_directory(client: AsyncClient, caseworker_user):
    # 1. Create a provider in the reusable pool
    provider_res = await client.post(
        "/api/v1/providers",
        json={
            "name": "Dr. Emily Stonechild",
            "provider_type": "Physician",
            "organization_name": "Regina Indigenous Health Centre",
            "phone": "306-555-0144",
        },
        headers=caseworker_user["headers"],
    )
    assert provider_res.status_code == 201
    provider_id = provider_res.json()["id"]

    # 2. Create a school in the directory
    school_res = await client.post(
        "/api/v1/schools",
        json={
            "name": "Wascana Community School",
            "school_type": "Elementary",
            "city": "Regina",
            "principal_name": "Mr. Dave Johnson",
        },
        headers=caseworker_user["headers"],
    )
    assert school_res.status_code == 201
    school_id = school_res.json()["id"]

    # 3. Create a client and link provider & school
    client_res = await client.post(
        "/api/v1/clients",
        json={"first_name": "Kaya", "last_name": "Bird", "status": "Active"},
        headers=caseworker_user["headers"],
    )
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    # Link provider
    link_res = await client.post(
        f"/api/v1/clients/{client_id}/providers",
        json={"provider_id": provider_id, "role": "Pediatrician"},
        headers=caseworker_user["headers"],
    )
    assert link_res.status_code == 201

    # Enroll in school
    enroll_res = await client.post(
        f"/api/v1/clients/{client_id}/schools",
        json={"school_id": school_id, "grade_level": "Grade 3", "has_iep": True},
        headers=caseworker_user["headers"],
    )
    assert enroll_res.status_code == 201
    assert enroll_res.json()["has_iep"] is True
