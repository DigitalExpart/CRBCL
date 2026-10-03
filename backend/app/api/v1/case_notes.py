"""Case note management endpoints with Phase 4 extensions: Draft/Complete/Lock lifecycle, Addenda, Cloning, Metrics, and Exports."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_any_permission, require_permission
from app.permissions.service import PermissionService
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
from app.services.speech_service import SpeechService

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


@router.post(
    "/case-notes/{note_id}/addenda", response_model=CaseNoteAddendumResponse, status_code=status.HTTP_201_CREATED
)
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


@router.get("/cases/{case_id}/notes/transcribe/status")
async def get_case_note_transcription_status(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_NOTE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Return availability and configuration status of the speech-to-text service for Case Notes."""
    case_service = CaseService(db)
    await case_service.get_case_or_404(case_id, user)
    service = SpeechService(db)
    return service.get_status()


@router.post("/cases/{case_id}/notes/transcribe")
async def transcribe_case_note_audio(
    case_id: uuid.UUID,
    response: Response,
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    purpose: str = Form(default="case_note"),
    note_id: uuid.UUID | None = Form(default=None),
    user: User = Depends(require_any_permission(Permissions.CASE_NOTE_CREATE, Permissions.CASE_NOTE_ADDENDUM)),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe in-memory audio recording for drafting assistance in a Case Note or Addendum.

    STRICT ARCHITECTURAL SEPARATION:
    Transcribe != Save Case Note or Addendum.
    This endpoint:
    - NEVER creates, updates, signs, finalizes, or publishes a Case Note or Addendum.
    - NEVER retains or persists raw audio.
    - NEVER persists transcript narrative in audit logs.
    - Requires case-level authorization and validated context capability:
      * purpose="case_note" -> requires CASE_NOTE_CREATE permission.
      * purpose="addendum"  -> requires CASE_NOTE_ADDENDUM permission, valid target note_id belonging to case_id.
    """
    # Defensive role boundary check: pure administrative or non-case roles cannot transcribe
    user_role_keys = {ur.role.key for ur in user.roles if ur.role and ur.role.is_active}
    prohibited_roles_alone = {"it_admin", "office_coordinator", "front_desk", "board_member"}
    if user_role_keys and user_role_keys.issubset(prohibited_roles_alone):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "ROLE_ACCESS_DENIED", "message": "Role is not authorized for Case Note operations."}},
        )

    perm_service = PermissionService(db)
    normalized_purpose = (purpose or "").strip().lower()

    if normalized_purpose == "case_note":
        if not await perm_service.user_has_permission(user.id, Permissions.CASE_NOTE_CREATE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "PERMISSION_DENIED", "message": f"User does not have required permission: {Permissions.CASE_NOTE_CREATE}"}},
            )
    elif normalized_purpose == "addendum":
        if not await perm_service.user_has_permission(user.id, Permissions.CASE_NOTE_ADDENDUM):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "PERMISSION_DENIED", "message": f"User does not have required permission: {Permissions.CASE_NOTE_ADDENDUM}"}},
            )
        if not note_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "NOTE_ID_REQUIRED", "message": "note_id is required for addendum transcription context."}},
            )
        # Verify target note exists, is not deleted, and current user is not restricted from note's case
        note_service = CaseNoteService(db)
        target_note = await note_service.get_note_or_404(note_id, user)
        if target_note.case_id != case_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_NOTE_CASE", "message": "Target note does not belong to the specified case."}},
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_PURPOSE", "message": f"Invalid transcription purpose '{purpose}'. Must be 'case_note' or 'addendum'."}},
        )

    # In-memory read of uploaded audio buffer
    audio_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"

    speech_service = SpeechService(db)
    result = await speech_service.transcribe_case_note_audio(
        case_id=case_id,
        audio_bytes=audio_bytes,
        content_type=content_type,
        current_user=user,
        language=language,
        purpose=normalized_purpose,
        note_id=note_id if normalized_purpose == "addendum" else None,
    )

    # Privacy controls: Prevent proxy or shared cache storage of transcription result
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"

    return result
