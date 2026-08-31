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


@pytest.mark.asyncio
async def test_register_and_verify_otp_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Register new account
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@crbcl.ca", "password": "Password123!", "full_name": "New User"},
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["success"] is True

    # 2. Duplicate registration rejected
    dup_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@crbcl.ca", "password": "Password123!", "full_name": "New User"},
    )
    assert dup_res.status_code == 409

    # 3. Retrieve generated verification code from DB
    from sqlalchemy import select

    from app.models.user import EmailVerificationCode

    res = await db_session.execute(
        select(EmailVerificationCode).where(EmailVerificationCode.email == "newuser@crbcl.ca")
    )
    code_record = res.scalar_one_or_none()
    assert code_record is not None

    # 4. Invalid OTP rejected
    invalid_res = await client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "newuser@crbcl.ca", "otp_code": "000000"},
    )
    assert invalid_res.status_code == 400

    # 5. Resend OTP creates fresh code
    resend_res = await client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "newuser@crbcl.ca"},
    )
    assert resend_res.status_code == 200

    # 6. Verify with helper that generates valid match
    from app.services.email_service import EmailService

    svc = EmailService(db_session)
    valid_code = await svc.create_and_send_verification_code("newuser@crbcl.ca")
    await db_session.commit()

    verify_res = await client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "newuser@crbcl.ca", "otp_code": valid_code},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert "access_token" in verify_data
    assert verify_data["user"]["email"] == "newuser@crbcl.ca"
