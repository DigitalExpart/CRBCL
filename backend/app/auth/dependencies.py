"""FastAPI dependencies for authentication."""

from __future__ import annotations

import uuid

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.auth.service import AuthService
from app.core.database import get_db
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias="crbcl_access_token"),
) -> User:
    """Extract and validate the current user from cookie or Authorization header."""
    token = access_token

    # Fallback to Authorization header (for API/mobile clients)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AUTH_REQUIRED", "message": "Authentication required"}},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired token"}},
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token payload"}},
        ) from None

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "USER_INACTIVE", "message": "Account is disabled"}},
        )

    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Alias for get_current_user — ensures user is active."""
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias="crbcl_access_token"),
) -> User | None:
    """Like get_current_user but returns None instead of raising."""
    try:
        return await get_current_user(request, db, access_token)
    except HTTPException:
        return None
