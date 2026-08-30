"""Authentication test suite."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    # Setup test user
    user = User(
        email="testlogin@crbcl.ca",
        email_normalized="testlogin@crbcl.ca",
        password_hash=hash_password("Secret123!"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testlogin@crbcl.ca", "password": "Secret123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testlogin@crbcl.ca"
    assert "crbcl_access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_failure_invalid_password(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="testfail@crbcl.ca",
        email_normalized="testfail@crbcl.ca",
        password_hash=hash_password("Secret123!"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testfail@crbcl.ca", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_inactive_user_rejected(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="inactive@crbcl.ca",
        email_normalized="inactive@crbcl.ca",
        password_hash=hash_password("Secret123!"),
        full_name="Inactive User",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@crbcl.ca", "password": "Secret123!"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_INACTIVE"


@pytest.mark.asyncio
async def test_unauthenticated_protected_endpoint_rejected(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_me_endpoint_with_auth(client: AsyncClient, caseworker_user):
    response = await client.get("/api/v1/auth/me", headers=caseworker_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "worker@crbcl.ca"
    assert "caseworker" in data["roles"]


@pytest.mark.asyncio
async def test_logout_clears_cookies(client: AsyncClient, caseworker_user):
    response = await client.post("/api/v1/auth/logout", headers=caseworker_user["headers"])
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
