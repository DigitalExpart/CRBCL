"""Case note management endpoints."""

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
from app.repositories.case_note_repo import CaseNoteRepository
from app.repositories.case_repo import CaseRepository
from app.schemas.case_note import CaseNoteBase, CaseNoteCreate, CaseNoteResponse
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineEventType, TimelineService

router = APIRouter(tags=["Case Notes"])


@router.get("/cases/{case_id}/notes", response_model=PaginatedResponse[CaseNoteResponse])
async def list_case_notes(
    case_id: uuid.UUID,
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.CASE_NOTE_READ)),
    db: AsyncSession = Depends(get_db),
):
    case_repo = CaseRepository(db)
    case_item = await case_repo.get(case_id)
    if not case_item or case_item.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Parent case not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, case_item.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Access restricted to assigned team"}},
        )

    note_repo = CaseNoteRepository(db)
    notes, total = await note_repo.list_for_case(
        case_id=case_id,
        include_confidential=True,
        offset=offset,
        limit=limit,
    )

    return PaginatedResponse[CaseNoteResponse](
        items=[CaseNoteResponse.model_validate(n) for n in notes],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.post("/cases/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_case_note(
    case_id: uuid.UUID,
    payload: CaseNoteBase,
    request: Request,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    case_repo = CaseRepository(db)
    case_item = await case_repo.get(case_id)
    if not case_item or case_item.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": "Parent case not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, case_item.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Unauthorized to add notes to this case"}},
        )

    note_repo = CaseNoteRepository(db)
    note_data = payload.model_dump()
    note_data["case_id"] = case_id
    note_data["created_by"] = user.id
    note_data["updated_by"] = user.id
    note_data["author_name"] = user.full_name or user.email

    # Transactional execution:
    # 1. Insert Case Note
    note = await note_repo.create(**note_data)

    # 2. Insert Audit Event
    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="CASE_NOTE_CREATED",
        user_id=user.id,
        entity_type="case_note",
        entity_id=note.id,
        after_data={
            "case_id": str(case_id),
            "note_type": note.note_type,
            "subject": note.subject,
            "is_confidential": note.is_confidential,
        },
        ip_address=request.client.host if request.client else None,
    )

    # 3. Insert Sacred Timeline Event
    timeline_service = TimelineService(db)
    await timeline_service.record_event(
        event_type=TimelineEventType.CASE_NOTE_ADDED,
        title=f"Case Note Added ({note.note_type})",
        description=f"Added by {note.author_name}: {note.subject or 'Progress update'}",
        entity_type="case_note",
        entity_id=note.id,
        case_id=case_id,
        client_id=case_item.client_id,
        family_id=case_item.family_id,
        created_by=user.id,
    )

    # 4. Insert Transactional Outbox Event
    outbox_service = OutboxService(db)
    await outbox_service.enqueue(
        event_type="CASE_NOTE_ADDED_NOTIFICATION",
        aggregate_type="case_note",
        aggregate_id=note.id,
        payload={
            "case_id": str(case_id),
            "case_note_id": str(note.id),
            "note_type": note.note_type,
            "author_name": note.author_name,
        },
    )

    # 5. Single COMMIT
    await db.commit()
    return CaseNoteResponse.model_validate(note)


@router.get("/case-notes/{note_id}", response_model=CaseNoteResponse)
async def get_case_note(
    note_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_READ)),
    db: AsyncSession = Depends(get_db),
):
    note_repo = CaseNoteRepository(db)
    note = await note_repo.get(note_id)
    if not note or note.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOTE_NOT_FOUND", "message": "Case note not found"}},
        )

    case_repo = CaseRepository(db)
    case_item = await case_repo.get(note.case_id)
    if case_item:
        perm_service = PermissionService(db)
        if not await perm_service.user_can_access_team(user.id, case_item.assigned_team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Access restricted to assigned team"}},
            )

    return CaseNoteResponse.model_validate(note)
