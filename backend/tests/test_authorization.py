"""Authorization and team-scoping test suite."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_caseworker_allowed_to_read_clients(client: AsyncClient, caseworker_user):
    response = await client.get("/api/v1/clients", headers=caseworker_user["headers"])
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_it_admin_denied_from_client_records(client: AsyncClient, it_admin_user):
    """
    CRITICAL SECURITY TEST:
    IT Admin must NOT automatically gain access to client/case records
    simply because they administer technical systems.
    """
    response = await client.get("/api/v1/clients", headers=it_admin_user["headers"])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_it_admin_allowed_to_manage_users(client: AsyncClient, it_admin_user):
    response = await client.get("/api/v1/users", headers=it_admin_user["headers"])
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_caseworker_denied_from_user_admin(client: AsyncClient, caseworker_user):
    response = await client.get("/api/v1/users", headers=caseworker_user["headers"])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
