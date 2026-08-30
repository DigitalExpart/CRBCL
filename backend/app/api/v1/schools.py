"""School directory endpoints."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.school_repo import SchoolRepository

router = APIRouter(prefix="/schools", tags=["Schools"])


class SchoolCreate(BaseModel):
    name: str
    school_type: str = "Elementary"
    district: str | None = None
    address: str | None = None
    city: str = "Regina"
    province: str = "Saskatchewan"
    postal_code: str | None = None
    phone: str | None = None
    principal_name: str | None = None
    contact_email: str | None = None
    notes: str | None = None


@router.get("")
async def list_schools(
    query: str | None = Query(default=None),
    school_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.SCHOOL_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolRepository(db)
    schools, total = await repo.list_schools(
        query_text=query, school_type=school_type, offset=offset, limit=limit
    )
    return {"items": schools, "total": total, "offset": offset, "limit": limit}


@router.get("/{school_id}")
async def get_school(
    school_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.SCHOOL_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolRepository(db)
    school = await repo.get(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SCHOOL_NOT_FOUND", "message": "School not found"}},
        )
    return school


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_school(
    payload: SchoolCreate,
    user: User = Depends(require_permission(Permissions.SCHOOL_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolRepository(db)
    school = await repo.create(**payload.model_dump())
    await db.commit()
    return school
