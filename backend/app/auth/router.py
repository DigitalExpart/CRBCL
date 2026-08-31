"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResendOtpRequest,
    ResetPasswordRequest,
    UserInfo,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.auth.security import generate_csrf_token, get_cookie_settings
from app.auth.service import AuthService
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str | None = None) -> None:
    """Set HttpOnly auth cookies and readable CSRF cookie for web clients."""
    settings = get_settings()
    cookie = get_cookie_settings(is_csrf=False)
    response.set_cookie(
        key="crbcl_access_token",
        value=access_token,
        max_age=settings.access_token_ttl,
        **cookie,
    )
    response.set_cookie(
        key="crbcl_refresh_token",
        value=refresh_token,
        max_age=settings.refresh_token_ttl,
        **cookie,
    )
    if csrf_token:
        csrf_cookie = get_cookie_settings(is_csrf=True)
        response.set_cookie(
            key="crbcl_csrf_token",
            value=csrf_token,
            max_age=settings.refresh_token_ttl,
            **csrf_cookie,
        )


def _clear_auth_cookies(response: Response) -> None:
    cookie = get_cookie_settings(is_csrf=False)
    csrf_cookie = get_cookie_settings(is_csrf=True)
    response.delete_cookie(key="crbcl_access_token", **cookie)
    response.delete_cookie(key="crbcl_refresh_token", **cookie)
    response.delete_cookie(key="crbcl_csrf_token", **csrf_cookie)


def _build_user_info(user: User) -> UserInfo:
    roles = [ur.role.key for ur in user.roles if ur.role and ur.role.is_active]
    permissions = set()
    for ur in user.roles:
        if ur.role and ur.role.is_active:
            for rp in ur.role.permissions:
                if rp.permission and rp.permission.is_active:
                    permissions.add(rp.permission.key)
    return UserInfo(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=roles,
        permissions=sorted(permissions),
        team_access=["all"] if "admin.users.manage" in permissions else [],
        created_at=user.created_at,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    auth = AuthService(db)
    user = await auth.authenticate(body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "USER_INACTIVE", "message": "Account is disabled"}},
        )

    access_token, refresh_token = await auth.create_session(
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    csrf_token = generate_csrf_token()
    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    settings = get_settings()
    return LoginResponse(
        access_token=access_token,
        expires_in=settings.access_token_ttl,
        user=_build_user_info(user),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    crbcl_refresh_token: str | None = Cookie(default=None),
):
    if not crbcl_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "NO_REFRESH_TOKEN", "message": "No refresh token provided"}},
        )

    auth = AuthService(db)
    result = await auth.refresh_session(crbcl_refresh_token)
    if not result:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"}},
        )

    access_token, new_refresh_token = result
    await db.commit()

    csrf_token = generate_csrf_token()
    _set_auth_cookies(response, access_token, new_refresh_token, csrf_token)

    settings = get_settings()
    return RefreshResponse(access_token=access_token, expires_in=settings.access_token_ttl)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    crbcl_refresh_token: str | None = Cookie(default=None),
):
    if crbcl_refresh_token:
        auth = AuthService(db)
        await auth.revoke_session(crbcl_refresh_token)
        await db.commit()
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserInfo)
async def me(user: User = Depends(get_current_user)):
    return _build_user_info(user)


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    existing = await auth.get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "EMAIL_EXISTS", "message": "An account with this email already exists"}},
        )
    user = await auth.register_user(body.email, body.password, body.full_name)
    
    # Generate and dispatch 6-digit verification code
    email_service = EmailService(db)
    await email_service.create_and_send_verification_code(body.email)
    
    await db.commit()
    return RegisterResponse(user_id=user.id, email=body.email)


@router.post("/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp(
    request: Request,
    response: Response,
    body: VerifyOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    email_service = EmailService(db)
    is_valid = await email_service.verify_otp(body.email, body.otp_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_OTP", "message": "Invalid or expired verification code"}},
        )

    auth = AuthService(db)
    user = await auth.get_user_by_email(body.email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User account not found or disabled"}},
        )

    access_token, refresh_token = await auth.create_session(
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    csrf_token = generate_csrf_token()
    _set_auth_cookies(response, access_token, refresh_token, csrf_token)
    await db.commit()

    # Refresh user with roles/permissions loaded
    user = await auth.get_user_by_id(user.id)
    settings = get_settings()
    return VerifyOtpResponse(
        access_token=access_token,
        expires_in=settings.access_token_ttl,
        user=_build_user_info(user),
    )


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(body: ResendOtpRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    user = await auth.get_user_by_email(body.email)
    if not user:
        return MessageResponse(message="If the account exists, a new verification code has been dispatched.")

    email_service = EmailService(db)
    await email_service.create_and_send_verification_code(body.email)
    await db.commit()
    return MessageResponse(message="Verification code sent to your email address")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return MessageResponse(message="If an account exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return MessageResponse(message="Password reset is not yet fully implemented")
