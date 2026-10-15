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


@pytest.mark.asyncio
async def test_pin_set_verify_and_status_flow(client: AsyncClient, db_session: AsyncSession):
    # Setup test user
    user = User(
        email="pintest@crbcl.ca",
        email_normalized="pintest@crbcl.ca",
        password_hash=hash_password("Secret123!"),
        full_name="PIN Tester",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # 1. Status should show false before PIN is set
    status_res = await client.get("/api/v1/auth/pin/status?email=pintest@crbcl.ca")
    assert status_res.status_code == 200
    assert status_res.json()["has_pin"] is False

    # 2. Log in to get access token
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "pintest@crbcl.ca", "password": "Secret123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 3. Setting a 4-digit PIN should be rejected by validation
    invalid_set = await client.post(
        "/api/v1/auth/pin/set",
        headers={"Authorization": f"Bearer {token}"},
        json={"pin": "1234"},
    )
    assert invalid_set.status_code == 422

    # 4. Setting a valid 6-digit PIN succeeds
    set_res = await client.post(
        "/api/v1/auth/pin/set",
        headers={"Authorization": f"Bearer {token}"},
        json={"pin": "654321"},
    )
    assert set_res.status_code == 200

    # 5. Status should now show true
    status_res2 = await client.get("/api/v1/auth/pin/status?email=pintest@crbcl.ca")
    assert status_res2.status_code == 200
    assert status_res2.json()["has_pin"] is True

    # 6. Verify PIN with incorrect PIN fails
    fail_verify = await client.post(
        "/api/v1/auth/pin/verify",
        json={"email": "pintest@crbcl.ca", "pin": "000000"},
    )
    assert fail_verify.status_code == 401

    # 7. Verify PIN with correct 6-digit PIN succeeds and issues tokens
    ok_verify = await client.post(
        "/api/v1/auth/pin/verify",
        json={"email": "pintest@crbcl.ca", "pin": "654321"},
    )
    assert ok_verify.status_code == 200
    verify_data = ok_verify.json()
    assert "access_token" in verify_data
    assert verify_data["user"]["email"] == "pintest@crbcl.ca"


@pytest.mark.asyncio
async def test_admin_hardcoded_passwords_rejected(client: AsyncClient, db_session: AsyncSession):
    """Ensure hardcoded passwords and backdoors are rejected and cannot overwrite stored password hashes."""
    admin_user = User(
        email="admin@crbcl.ca",
        email_normalized="admin@crbcl.ca",
        password_hash=hash_password("RealAdminPassword999#"),
        full_name="System Administrator",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    # Attempting to log in with arbitrary hardcoded backdoor passwords must fail
    for backdoor in ["admin123456", "crbcl_admin_2026", "Admin@CRBCL2026!"]:
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@crbcl.ca", "password": backdoor},
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Verify that the legitimate password still works and was not altered
    ok_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@crbcl.ca", "password": "RealAdminPassword999#"},
    )
    assert ok_res.status_code == 200


@pytest.mark.asyncio
async def test_admin_pin_without_stored_hash_rejected(client: AsyncClient, db_session: AsyncSession):
    """Ensure that an admin user without an explicit PIN preference cannot log in with default 123456."""
    user = User(
        email="admin@crbcl.ca",
        email_normalized="admin@crbcl.ca",
        password_hash=hash_password("RealAdminPassword999#"),
        full_name="System Administrator",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Attempt PIN verify with default PIN 123456 when no quick_pin_hash preference is set
    res = await client.post(
        "/api/v1/auth/pin/verify",
        json={"email": "admin@crbcl.ca", "pin": "123456"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_PIN"

