"""Family management endpoints with members, relationships, genogram, and map views."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.repositories.family_repo import FamilyRepository
from app.repositories.relationship_repo import RelationshipRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.family import FamilyCreate, FamilyResponse, FamilyUpdate
from app.services.genogram_service import GenogramService
from app.workflows.timeline import TimelineEventType, TimelineService

router = APIRouter(prefix="/families", tags=["Families"])


# ── Family Sub-Schemas ───────────────────────────────────────

class FamilyMemberCreate(BaseModel):
    person_id: uuid.UUID
    role: str = "Member"
    start_date: date | None = None
    notes: str = ""


class RelationshipCreate(BaseModel):
    person_a_id: uuid.UUID
    person_b_id: uuid.UUID
    relationship_type: str
    notes: str = ""


# ── Family Endpoints ─────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[FamilyResponse])
async def list_families(
    request: Request,
    query: str | None = Query(default=None, description="Search family name or contact"),
    status_filter: str | None = Query(default=None, alias="status"),
    risk_level: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sort: str | None = Query(default=None),
    user: User = Depends(require_permission(Permissions.FAMILY_READ)),
    db: AsyncSession = Depends(get_db),
):
    perm_service = PermissionService(db)
    accessible_team_ids = await perm_service.get_user_accessible_team_ids(user.id)

    repo = FamilyRepository(db)
    families, total = await repo.search(
        query_text=query,
        status=status_filter,
        risk_level=risk_level,
        accessible_team_ids=accessible_team_ids,
        offset=offset,
        limit=limit,
        sort_by=sort,
    )

    return PaginatedResponse[FamilyResponse](
        items=[FamilyResponse.model_validate(f) for f in families],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_permission(Permissions.FAMILY_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = FamilyRepository(db)
    family = await repo.get(family_id)
    if not family or family.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FAMILY_NOT_FOUND", "message": "Family not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, family.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Access restricted to assigned team"}},
        )

    return FamilyResponse.model_validate(family)


@router.post("", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    payload: FamilyCreate,
    request: Request,
    user: User = Depends(require_permission(Permissions.FAMILY_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = FamilyRepository(db)
    family_data = payload.model_dump()
    family_data["created_by"] = user.id
    family_data["updated_by"] = user.id

    family = await repo.create(**family_data)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="FAMILY_CREATED",
        user_id=user.id,
        entity_type="family",
        entity_id=family.id,
        after_data=payload.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
    )

    timeline_service = TimelineService(db)
    await timeline_service.record_event(
        event_type=TimelineEventType.FAMILY_CREATED,
        title=f"Family File Opened: {family.family_name}",
        description=f"Primary Contact: {family.primary_contact_name or 'Not specified'}, Members: {family.total_members}",
        entity_type="family",
        entity_id=family.id,
        family_id=family.id,
        created_by=user.id,
    )

    await db.commit()
    return FamilyResponse.model_validate(family)


@router.patch("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: uuid.UUID,
    payload: FamilyUpdate,
    request: Request,
    user: User = Depends(require_permission(Permissions.FAMILY_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = FamilyRepository(db)
    family = await repo.get(family_id)
    if not family or family.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "FAMILY_NOT_FOUND", "message": "Family not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, family.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Unauthorized to update this family"}},
        )

    before_data = FamilyResponse.model_validate(family).model_dump(mode="json")
    update_data = payload.model_dump(exclude_unset=True)
    update_data["updated_by"] = user.id

    updated_family = await repo.update(family, **update_data)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="FAMILY_UPDATED",
        user_id=user.id,
        entity_type="family",
        entity_id=family.id,
        before_data=before_data,
        after_data=update_data,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return FamilyResponse.model_validate(updated_family)


# ── Family Members & Relationships ───────────────────────────

@router.get("/{family_id}/members")
async def list_family_members(
    family_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.FAMILY_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = RelationshipRepository(db)
    members = await repo.list_family_members(family_id)
    return members


@router.post("/{family_id}/members", status_code=status.HTTP_201_CREATED)
async def add_family_member(
    family_id: uuid.UUID,
    payload: FamilyMemberCreate,
    user: User = Depends(require_permission(Permissions.FAMILY_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = RelationshipRepository(db)
    member = await repo.add_family_member(
        family_id=family_id,
        person_id=payload.person_id,
        role=payload.role,
        notes=payload.notes,
    )
    await db.commit()
    return member


@router.get("/{family_id}/relationships")
async def list_family_relationships(
    family_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.FAMILY_RELATIONSHIPS_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = RelationshipRepository(db)
    relationships = await repo.list_family_relationships(family_id=family_id)
    return relationships


@router.post("/{family_id}/relationships", status_code=status.HTTP_201_CREATED)
async def create_family_relationship(
    family_id: uuid.UUID,
    payload: RelationshipCreate,
    user: User = Depends(require_permission(Permissions.FAMILY_RELATIONSHIPS_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = RelationshipRepository(db)
    rel = await repo.add_relationship(
        person_a_id=payload.person_a_id,
        person_b_id=payload.person_b_id,
        relationship_type=payload.relationship_type,
        family_id=family_id,
        notes=payload.notes,
    )
    await db.commit()
    return rel


@router.get("/{family_id}/genogram")
async def get_family_genogram(
    family_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.FAMILY_RELATIONSHIPS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Fetch Genogram graph structure for visualization."""
    service = GenogramService(db)
    genogram = await service.get_family_genogram(family_id)
    return genogram


@router.get("/{family_id}/map")
async def get_family_map_locations(
    family_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.HOUSEHOLD_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Fetch pin locations for family households and dwellings."""
    service = GenogramService(db)
    genogram = await service.get_family_genogram(family_id)
    households = genogram.get("households", [])
    valid_locations = [h for h in households if h.get("latitude") is not None and h.get("longitude") is not None]
    return {"family_id": str(family_id), "locations": valid_locations}
