"""Household management endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.household_repo import HouseholdRepository

router = APIRouter(prefix="/households", tags=["Households"])


class HouseholdCreate(BaseModel):
    name: str
    address_line_1: str
    address_line_2: str | None = None
    city: str = "Regina"
    province: str = "Saskatchewan"
    postal_code: str | None = None
    on_reserve: bool = False
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    notes: str | None = None


class HouseholdMemberAdd(BaseModel):
    person_id: uuid.UUID
    role: str = "Resident"
    notes: str = ""


@router.get("")
async def list_households(
    query: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.HOUSEHOLD_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = HouseholdRepository(db)
    households, total = await repo.list_households(query_text=query, offset=offset, limit=limit)
    return {"items": households, "total": total, "offset": offset, "limit": limit}


@router.get("/{household_id}")
async def get_household(
    household_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.HOUSEHOLD_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = HouseholdRepository(db)
    household = await repo.get_with_members(household_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "HOUSEHOLD_NOT_FOUND", "message": "Household not found"}},
        )
    return household


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_household(
    payload: HouseholdCreate,
    user: User = Depends(require_permission(Permissions.HOUSEHOLD_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = HouseholdRepository(db)
    household = await repo.create(**payload.model_dump())
    await db.commit()
    return household


@router.post("/{household_id}/members", status_code=status.HTTP_201_CREATED)
async def add_household_member(
    household_id: uuid.UUID,
    payload: HouseholdMemberAdd,
    user: User = Depends(require_permission(Permissions.HOUSEHOLD_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = HouseholdRepository(db)
    membership = await repo.add_member(
        household_id=household_id,
        person_id=payload.person_id,
        role=payload.role,
        notes=payload.notes,
    )
    await db.commit()
    return membership
