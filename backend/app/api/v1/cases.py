"""Case management endpoints."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.repositories.case_repo import CaseRepository
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineEventType, TimelineService

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=PaginatedResponse[CaseResponse])
async def list_cases(
    request: Request,
    query: str | None = Query(default=None, description="Search case #, title, worker"),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    case_type: str | None = Query(default=None),
    client_id: uuid.UUID | None = Query(default=None),
    family_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sort: str | None = Query(default=None),
    user: User = Depends(require_permission(Permissions.CASE_READ)),
    db: AsyncSession = Depends(get_db),
):
    perm_service = PermissionService(db)
    accessible_team_ids = await perm_service.get_user_accessible_team_ids(user.id)

    repo = CaseRepository(db)
    cases, total = await repo.search(
        query_text=query,
        status=status_filter,
        priority=priority,
        case_type=case_type,
        client_id=client_id,
        family_id=family_id,
        accessible_team_ids=accessible_team_ids,
        offset=offset,
        limit=limit,
        sort_by=sort,
    )

    return PaginatedResponse[CaseResponse](
        items=[CaseResponse.model_validate(c) for c in cases],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_permission(Permissions.CASE_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = CaseRepository(db)
    case_item = await repo.get(case_id)
    if not case_item or case_item.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, case_item.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Access restricted to assigned team"}},
        )

    return CaseResponse.model_validate(case_item)


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    request: Request,
    user: User = Depends(require_permission(Permissions.CASE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = CaseRepository(db)
    case_data = payload.model_dump()

    # Auto-generate case number if not provided
    if not case_data.get("case_number"):
        case_data["case_number"] = await repo.generate_case_number()

    case_data["created_by"] = user.id
    case_data["updated_by"] = user.id

    case_item = await repo.create(**case_data)

    # 1. Audit event
    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="CASE_OPENED",
        user_id=user.id,
        entity_type="case",
        entity_id=case_item.id,
        after_data=case_data,
        ip_address=request.client.host if request.client else None,
    )

    # 2. Sacred Timeline event
    timeline_service = TimelineService(db)
    await timeline_service.record_event(
        event_type=TimelineEventType.CASE_OPENED,
        title=f"Case Opened: {case_item.case_number} — {case_item.title}",
        description=f"Type: {case_item.case_type or 'General'}, Priority: {case_item.priority}",
        entity_type="case",
        entity_id=case_item.id,
        case_id=case_item.id,
        client_id=case_item.client_id,
        family_id=case_item.family_id,
        created_by=user.id,
    )

    # 3. Transactional outbox event
    outbox_service = OutboxService(db)
    await outbox_service.enqueue(
        event_type="CASE_CREATED_NOTIFICATION",
        aggregate_type="case",
        aggregate_id=case_item.id,
        payload={
            "case_id": str(case_item.id),
            "case_number": case_item.case_number,
            "title": case_item.title,
            "assigned_worker_id": str(case_item.assigned_worker_id) if case_item.assigned_worker_id else None,
        },
    )

    await db.commit()
    return CaseResponse.model_validate(case_item)


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    request: Request,
    user: User = Depends(require_permission(Permissions.CASE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = CaseRepository(db)
    case_item = await repo.get(case_id)
    if not case_item or case_item.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Case not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, case_item.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Unauthorized to update this case"}},
        )

    before_data = CaseResponse.model_validate(case_item).model_dump(mode="json")
    update_data = payload.model_dump(exclude_unset=True)
    update_data["updated_by"] = user.id

    updated_case = await repo.update(case_item, **update_data)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="CASE_UPDATED",
        user_id=user.id,
        entity_type="case",
        entity_id=case_item.id,
        before_data=before_data,
        after_data=update_data,
        ip_address=request.client.host if request.client else None,
    )

    # Check status changes for Timeline
    event_type = TimelineEventType.CASE_UPDATED
    if update_data.get("status") == "Closed" and before_data.get("status") != "Closed":
        event_type = TimelineEventType.CASE_CLOSED
    elif before_data.get("status") == "Closed" and update_data.get("status") in ("Open", "In Progress"):
        event_type = TimelineEventType.CASE_REOPENED

    timeline_service = TimelineService(db)
    await timeline_service.record_event(
        event_type=event_type,
        title=f"Case Updated: {updated_case.case_number}",
        description="Fields updated: " + ", ".join(update_data.keys()),
        entity_type="case",
        entity_id=updated_case.id,
        case_id=updated_case.id,
        client_id=updated_case.client_id,
        family_id=updated_case.family_id,
        created_by=user.id,
    )

    await db.commit()
    return CaseResponse.model_validate(updated_case)
