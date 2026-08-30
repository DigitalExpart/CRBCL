"""User administration endpoints."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.auth.security import hash_password
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.user_repo import UserRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _build_user_response(user: User) -> UserResponse:
    roles = [ur.role.key for ur in user.roles if ur.role and ur.role.is_active]
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        display_name=user.display_name,
        phone=user.phone,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=roles,
        team_access=["all"] if "admin.users.manage" in roles or "admin" in roles else [],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    query: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.ADMIN_USERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    users, total = await repo.list_users(query_text=query, offset=offset, limit=limit)

    return PaginatedResponse[UserResponse](
        items=[_build_user_response(u) for u in users],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.ADMIN_USERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    target_user = await repo.get_with_roles_and_teams(user_id)
    if not target_user or target_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    return _build_user_response(target_user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    request: Request,
    user: User = Depends(require_permission(Permissions.ADMIN_USERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    normalized = payload.email.strip().lower()

    # Check existence
    existing = await repo.list(filters={"email_normalized": normalized})
    if existing[0]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "EMAIL_EXISTS", "message": "User with this email already exists"}},
        )

    new_user = await repo.create(
        email=payload.email.strip(),
        email_normalized=normalized,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
        is_verified=True,
        created_by=user.id,
        updated_by=user.id,
    )

    if payload.role_keys:
        await repo.assign_roles(new_user.id, payload.role_keys, assigned_by=user.id)

    if payload.team_ids:
        await repo.assign_teams(new_user.id, payload.team_ids, assigned_by=user.id)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="USER_CREATED",
        user_id=user.id,
        entity_type="user",
        entity_id=new_user.id,
        after_data={"email": new_user.email, "roles": payload.role_keys},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    fresh = await repo.get_with_roles_and_teams(new_user.id)
    return _build_user_response(fresh)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    user: User = Depends(require_permission(Permissions.ADMIN_USERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    target = await repo.get_with_roles_and_teams(user_id)
    if not target or target.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    update_fields = payload.model_dump(exclude_unset=True, exclude={"role_keys", "team_ids"})
    update_fields["updated_by"] = user.id

    if update_fields:
        await repo.update(target, **update_fields)

    if payload.role_keys is not None:
        await repo.assign_roles(target.id, payload.role_keys, assigned_by=user.id)

    if payload.team_ids is not None:
        await repo.assign_teams(target.id, payload.team_ids, assigned_by=user.id)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="USER_UPDATED",
        user_id=user.id,
        entity_type="user",
        entity_id=target.id,
        after_data=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    fresh = await repo.get_with_roles_and_teams(target.id)
    return _build_user_response(fresh)
