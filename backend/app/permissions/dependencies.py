"""FastAPI dependencies for permission enforcement."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.service import PermissionService


def require_permission(permission_key: str) -> Callable:
    """Dependency factory checking that the authenticated user possesses the given permission."""

    async def permission_checker(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        perm_service = PermissionService(db)
        has_perm = await perm_service.user_has_permission(user.id, permission_key)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": f"User does not have required permission: {permission_key}",
                    }
                },
            )
        return user

    return permission_checker


def require_team_access() -> Callable:
    """Dependency checking that the authenticated user can access a specific team."""

    async def team_checker(
        team_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        perm_service = PermissionService(db)
        can_access = await perm_service.user_can_access_team(user.id, team_id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "TEAM_ACCESS_DENIED",
                        "message": "User is not authorized to access records for this team",
                    }
                },
            )
        return user

    return team_checker
