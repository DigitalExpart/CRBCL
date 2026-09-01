"""Tests for Conflict-of-Interest Case Restrictions (ADR-010) across Placement Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_case_restrictions_block_placement_access(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create standard caseworker user
    user_res = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "restricted_placement_worker@crbcl.ca",
            "password": "SecurePassword2026!",
            "full_name": "Restricted Placement Worker",
            "role": "caseworker",
        },
    )
    assert user_res.status_code == 201
    restricted_user_id = user_res.json()["id"]

    from app.auth.security import create_access_token

    worker_token = create_access_token(restricted_user_id)
    worker_headers = {"Authorization": f"Bearer {worker_token}"}
    client.cookies.clear()

    # 2. Admin creates client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={
            "first_name": "Restricted",
            "last_name": "ChildPlacement",
            "date_of_birth": "2018-01-01",
            "gender": "Female",
        },
    )
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Restricted Placement Case", "case_type": "Child Protection", "primary_client_id": person_id},
    )
    case_id = case_res.json()["id"]

    # 3. Create active effort, removal, and placement as Admin
    effort_res = await client.post(
        f"/api/v1/cases/{case_id}/active-efforts",
        headers=headers,
        json={"effort_type": "COUNSELING", "description": "Family counseling", "service_date": "2026-08-01"},
    )
    assert effort_res.status_code == 201
    effort_id = effort_res.json()["id"]

    placement_res = await client.post(
        f"/api/v1/cases/{case_id}/placements",
        headers=headers,
        json={
            "child_id": person_id,
            "placement_type": "KINSHIP",
            "provider_name": "Private Kinship Home",
            "start_date": "2026-08-01",
        },
    )
    assert placement_res.status_code == 201
    placement_id = placement_res.json()["id"]

    # 4. Place restriction on the caseworker for this case
    restr_res = await client.post(
        f"/api/v1/cases/{case_id}/restrictions",
        headers=headers,
        json={"user_id": restricted_user_id, "restriction_type": "CONFLICT_OF_INTEREST", "reason": "Close relative."},
    )
    assert restr_res.status_code == 201

    # 5. Worker attempts to read active efforts -> 403 Forbidden
    effort_read = await client.get(f"/api/v1/cases/{case_id}/active-efforts", headers=worker_headers)
    assert effort_read.status_code == 403
    assert "Case restriction active" in effort_read.text

    # 6. Worker attempts to read placement episode -> 403 Forbidden
    placement_read = await client.get(f"/api/v1/placements/{placement_id}", headers=worker_headers)
    assert placement_read.status_code == 403
    assert "Case restriction active" in placement_read.text

    # 7. Worker attempts to list case placements -> 403 Forbidden
    list_read = await client.get(f"/api/v1/cases/{case_id}/placements", headers=worker_headers)
    assert list_read.status_code == 403
    assert "Case restriction active" in list_read.text

    # 8. Worker attempts to schedule respite -> 403 Forbidden
    respite_create = await client.post(
        f"/api/v1/placements/{placement_id}/respite",
        headers=worker_headers,
        json={"respite_provider_name": "Test Respite", "start_date": "2026-08-10", "end_date": "2026-08-12"},
    )
    assert respite_create.status_code == 403
