"""Provider pool endpoints."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.provider_repo import ProviderRepository

router = APIRouter(prefix="/providers", tags=["Providers"])


class ProviderCreate(BaseModel):
    name: str
    provider_type: str
    organization_name: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    notes: str | None = None


class ProviderUpdate(BaseModel):
    name: str | None = None
    provider_type: str | None = None
    organization_name: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    is_active: bool | None = None
    notes: str | None = None


@router.get("")
async def list_providers(
    query: str | None = Query(default=None),
    provider_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.PROVIDER_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    providers, total = await repo.list_providers(
        query_text=query, provider_type=provider_type, offset=offset, limit=limit
    )
    return {"items": providers, "total": total, "offset": offset, "limit": limit}


@router.get("/{provider_id}")
async def get_provider(
    provider_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.PROVIDER_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROVIDER_NOT_FOUND", "message": "Provider not found"}},
        )
    return provider


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: ProviderCreate,
    user: User = Depends(require_permission(Permissions.PROVIDER_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = await repo.create(**payload.model_dump())
    await db.commit()
    return provider


@router.patch("/{provider_id}")
async def update_provider(
    provider_id: uuid.UUID,
    payload: ProviderUpdate,
    user: User = Depends(require_permission(Permissions.PROVIDER_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PROVIDER_NOT_FOUND", "message": "Provider not found"}},
        )
    updated = await repo.update(provider, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return updated
