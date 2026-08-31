"""Tests for Conflict-of-Interest Case Restrictions (ADR-010) on Plan Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_case_restrictions_block_plan_access(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create standard caseworker user
    user_res = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "restricted_plan_worker@crbcl.ca",
            "password": "SecurePassword2026!",
            "full_name": "Restricted Plan Worker",
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
        json={"first_name": "Restricted", "last_name": "ClientPlan", "date_of_birth": "2019-05-12", "gender": "Female"},
    )
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Restricted Conflict Case", "case_type": "Child Protection", "primary_client_id": person_id},
    )
    case_id = case_res.json()["id"]

    # 3. Create Plan on the case
    plan_res = await client.post(
        f"/api/v1/cases/{case_id}/plans",
        headers=headers,
        json={"case_id": case_id, "plan_type": "SAFETY_PLAN", "title": "Confidential Safety Plan"},
    )
    assert plan_res.status_code == 201
    plan_id = plan_res.json()["id"]

    # 4. Place conflict-of-interest restriction on the caseworker for this case
    restr_res = await client.post(
        f"/api/v1/cases/{case_id}/restrictions",
        headers=headers,
        json={"user_id": restricted_user_id, "restriction_type": "CONFLICT_OF_INTEREST", "reason": "Family relative."},
    )
    assert restr_res.status_code == 201

    # 5. Restricted worker attempts to read plans on case -> 403 Forbidden
    list_res = await client.get(f"/api/v1/cases/{case_id}/plans", headers=worker_headers)
    assert list_res.status_code == 403

    # 6. Restricted worker attempts direct access by plan UUID -> 403 Forbidden
    detail_res = await client.get(f"/api/v1/plans/{plan_id}", headers=worker_headers)
    assert detail_res.status_code == 403

    # 7. Restricted worker attempts to sign plan -> 403 Forbidden
    sig_res = await client.post(
        f"/api/v1/plans/{plan_id}/signatures",
        headers=worker_headers,
        json={"signer_type": "WORKER", "signer_name": "Restricted Worker", "signer_role": "Caseworker"},
    )
    assert sig_res.status_code == 403

    # 8. Restricted worker attempts to get active goals -> 403 Forbidden
    goals_res = await client.get(f"/api/v1/cases/{case_id}/active-goals", headers=worker_headers)
    assert goals_res.status_code == 403
