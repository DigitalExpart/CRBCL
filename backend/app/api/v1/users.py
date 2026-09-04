"""User administration endpoints."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.auth.security import hash_password
from app.core.database import get_db
from app.models.user import User, UserPreference
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.user_repo import UserRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _build_user_response(user: User) -> UserResponse:

    roles = [ur.role.key for ur in user.roles if ur.role and ur.role.is_active]

    # Check preferences for persisted team_access
    team_access = []
    if hasattr(user, "preferences") and user.preferences:
        pref = next((p for p in user.preferences if p.key == "team_access"), None)
        if pref and pref.value:
            try:
                loaded = json.loads(pref.value)
                if isinstance(loaded, list):
                    team_access = [str(x) for x in loaded]
            except Exception:
                team_access = []

    if not team_access and any(
        r in roles for r in ["executive_director", "it_admin", "director_manager", "admin"]
    ):
        team_access = ["all"]

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        display_name=user.display_name,
        phone=user.phone,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=roles,
        team_access=team_access,
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


@router.patch("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: uuid.UUID,
    role_key: str = Query(default="caseworker"),
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
    target_user.is_active = True
    target_user.is_verified = True
    await repo.assign_roles(target_user.id, [role_key], assigned_by=user.id)
    await db.commit()
    refreshed = await repo.get_with_roles_and_teams(user_id)
    return _build_user_response(refreshed)


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

    update_fields = payload.model_dump(exclude_unset=True, exclude={"role", "role_keys", "team_access", "team_ids"})
    update_fields["updated_by"] = user.id

    if update_fields:
        await repo.update(target, **update_fields)

    # Determine role keys from role_keys or role
    role_keys = payload.role_keys
    if role_keys is None and payload.role:
        role_keys = ["executive_director", "it_admin"] if payload.role == "admin" else [payload.role]

    if role_keys is not None:
        await repo.assign_roles(user_id, role_keys, assigned_by=user.id)

    if payload.team_access is not None:
        pref_res = await db.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.key == "team_access",
            )
        )
        pref = pref_res.scalars().first()
        raw_val = json.dumps(payload.team_access)
        if pref:
            pref.value = raw_val
        else:
            pref = UserPreference(user_id=user_id, key="team_access", value=raw_val)
            db.add(pref)

    if payload.team_ids is not None:
        await repo.assign_teams(user_id, payload.team_ids, assigned_by=user.id)

    await db.commit()
    fresh = await repo.get_with_roles_and_teams(user_id)
    return _build_user_response(fresh)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_permission(Permissions.ADMIN_USERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "CANNOT_DELETE_SELF", "message": "You cannot delete your own administrator account"}},
        )
    repo = UserRepository(db)
    target = await repo.get(user_id)
    if not target or target.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    await repo.soft_delete(target)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="USER_DELETED",
        user_id=user.id,
        entity_type="user",
        entity_id=user_id,
        after_data={"deleted_user_email": target.email},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return None
