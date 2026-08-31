"""Case note management endpoints with Phase 4 extensions: Draft/Complete/Lock lifecycle, Addenda, Cloning, Metrics, and Exports."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.case_note_repo import CaseNoteRepository
from app.schemas.case_management import (
    CaseMetricsResponse,
    CaseNoteAddendumCreate,
    CaseNoteAddendumResponse,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseNoteUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.case_note_service import CaseNoteService
from app.services.case_service import CaseService

router = APIRouter(tags=["Case Notes"])


@router.get("/cases/{case_id}/notes", response_model=PaginatedResponse[CaseNoteResponse])
async def list_case_notes(
    case_id: uuid.UUID,
    contact_type: str | None = Query(default=None),
    location: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    appointment_status: str | None = Query(default=None),
    author: str | None = Query(default=None),
    search: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    sort: str = Query(default="desc"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_permission(Permissions.CASE_NOTE_READ)),
    db: AsyncSession = Depends(get_db),
):
    case_service = CaseService(db)
    await case_service.get_case_or_404(case_id, user)

    note_repo = CaseNoteRepository(db)
    notes, total = await note_repo.list_for_case(
        case_id=case_id,
        include_confidential=True,
        contact_type=contact_type,
        location=location,
        status=status_filter,
        appointment_status=appointment_status,
        author_name=author,
        search=search,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort,
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
    payload: CaseNoteCreate,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    note = await service.create_note(
        case_id=case_id,
        subject=payload.subject,
        content=payload.content,
        note_type=payload.note_type,
        duration_minutes=payload.duration_minutes,
        contact_type=payload.contact_type,
        location=payload.location,
        is_well_child_checkup=payload.is_well_child_checkup,
        appointment_status=payload.appointment_status,
        next_appointment_at=payload.next_appointment_at,
        goal_id=payload.goal_id,
        notify_team=payload.notify_team,
        status_val=payload.status,
        is_confidential=payload.is_confidential,
        people_ids=payload.people_ids,
        current_user=user,
    )
    return CaseNoteResponse.model_validate(note)


@router.get("/case-notes/{note_id}", response_model=CaseNoteResponse)
async def get_case_note(
    note_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    note = await service.get_note_or_404(note_id, user)
    return CaseNoteResponse.model_validate(note)


@router.patch("/case-notes/{note_id}", response_model=CaseNoteResponse)
async def update_case_note(
    note_id: uuid.UUID,
    payload: CaseNoteUpdate,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    note = await service.update_note(
        note_id=note_id,
        update_data=payload.model_dump(exclude_unset=True),
        current_user=user,
    )
    return CaseNoteResponse.model_validate(note)


@router.post("/case-notes/{note_id}/complete", response_model=CaseNoteResponse)
async def complete_case_note(
    note_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_COMPLETE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    note = await service.complete_note(note_id=note_id, current_user=user)
    return CaseNoteResponse.model_validate(note)


@router.post("/case-notes/{note_id}/lock", response_model=CaseNoteResponse)
async def lock_case_note(
    note_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_LOCK)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    note = await service.lock_note(note_id=note_id, current_user=user)
    return CaseNoteResponse.model_validate(note)


@router.post("/case-notes/{note_id}/addenda", response_model=CaseNoteAddendumResponse, status_code=status.HTTP_201_CREATED)
async def add_case_note_addendum(
    note_id: uuid.UUID,
    payload: CaseNoteAddendumCreate,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_ADDENDUM)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    addendum = await service.add_addendum(
        note_id=note_id,
        content=payload.content,
        reason=payload.reason,
        current_user=user,
    )
    return CaseNoteAddendumResponse(
        id=addendum.id,
        case_note_id=addendum.case_note_id,
        content=addendum.content,
        reason=addendum.reason,
        created_by=addendum.created_by,
        author_name=(addendum.author.full_name if addendum.author else None) or user.full_name or user.email,
        created_at=addendum.created_at,
    )


@router.post("/case-notes/{note_id}/clone", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def clone_case_note(
    note_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    note = await service.clone_note(note_id=note_id, current_user=user)
    return CaseNoteResponse.model_validate(note)


@router.get("/cases/{case_id}/notes/metrics", response_model=CaseMetricsResponse)
async def get_case_note_metrics(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_READ)),
    db: AsyncSession = Depends(get_db),
):
    case_service = CaseService(db)
    await case_service.get_case_or_404(case_id, user)
    note_repo = CaseNoteRepository(db)
    metrics = await note_repo.get_case_metrics(case_id)
    return CaseMetricsResponse(**metrics)


@router.get("/cases/{case_id}/notes/export")
async def export_case_notes(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_EXPORT)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseNoteService(db)
    csv_data = await service.export_notes_csv(case_id=case_id, current_user=user)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=case_{case_id}_notes.csv"},
    )
