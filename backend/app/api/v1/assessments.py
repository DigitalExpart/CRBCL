"""API Router for Case Assessments, Answers, Locking, Director Unlock/Reassignment, and Comparisons."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.assessment import (
    AssessmentAnswersSaveRequest,
    AssessmentComparisonResponse,
    AssessmentCompleteRequest,
    AssessmentCreate,
    AssessmentDetailResponse,
    AssessmentLockRequest,
    AssessmentReassignRequest,
    AssessmentResponse,
    AssessmentUnlockRequest,
    AssessmentUpdate,
)
from app.services.assessment_service import AssessmentService

router = APIRouter(tags=["Assessments"])


def _to_detail_response(
    assessment: Assessment, indicator_summary: dict[str, Any] | None = None
) -> AssessmentDetailResponse:
    answers_resp = []
    for ans in assessment.answers:
        opt_ids = [opt.option_id for opt in ans.selected_options]
        opt_objs = [opt.option for opt in ans.selected_options if opt.option]
        answers_resp.append(
            {
                "id": ans.id,
                "assessment_id": ans.assessment_id,
                "question_id": ans.question_id,
                "question_key": ans.question.key if ans.question else None,
                "boolean_value": ans.boolean_value,
                "number_value": float(ans.number_value) if ans.number_value is not None else None,
                "text_value": ans.text_value,
                "date_value": ans.date_value,
                "datetime_value": ans.datetime_value,
                "json_value": ans.json_value,
                "notes": ans.notes,
                "selected_option_ids": opt_ids,
                "selected_options": opt_objs,
                "created_at": ans.created_at,
                "updated_at": ans.updated_at,
            }
        )

    return AssessmentDetailResponse(
        id=assessment.id,
        case_id=assessment.case_id,
        case_number=assessment.case.case_number if assessment.case else None,
        person_id=assessment.person_id,
        person_name=f"{assessment.person.first_name} {assessment.person.last_name}" if assessment.person else None,
        client_id=assessment.client_id,
        family_id=assessment.family_id,
        family_name=assessment.family.family_name if assessment.family else None,
        household_id=assessment.household_id,
        template_id=assessment.template_id,
        template_key=assessment.template.key if assessment.template else None,
        template_name=assessment.template.name if assessment.template else None,
        template_category=assessment.template.category if assessment.template else None,
        template_version_id=assessment.template_version_id,
        version_number=assessment.template_version.version_number if assessment.template_version else None,
        assessment_number=assessment.assessment_number,
        title=assessment.title,
        status=assessment.status,
        determination=assessment.determination,
        determination_notes=assessment.determination_notes,
        conducted_by=assessment.conducted_by,
        conducted_by_name=assessment.conductor.full_name or assessment.conductor.email
        if assessment.conductor
        else None,
        conducted_at=assessment.conducted_at,
        completed_at=assessment.completed_at,
        completed_by=assessment.completed_by,
        locked_at=assessment.locked_at,
        locked_by=assessment.locked_by,
        is_locked=assessment.status == "LOCKED",
        summary=assessment.summary,
        metadata_=assessment.metadata_,
        template_version=assessment.template_version,
        answers=answers_resp,
        status_history=[
            {
                "id": h.id,
                "assessment_id": h.assessment_id,
                "from_status": h.from_status,
                "to_status": h.to_status,
                "reason": h.reason,
                "created_by": h.created_by,
                "author_name": h.author.full_name if h.author else None,
                "created_at": h.created_at,
            }
            for h in assessment.status_history
        ],
        unlock_events=[
            {
                "id": u.id,
                "assessment_id": u.assessment_id,
                "unlocked_by": u.unlocked_by,
                "director_name": u.director.full_name if u.director else None,
                "reason": u.reason,
                "unlocked_at": u.unlocked_at,
            }
            for u in assessment.unlock_events
        ],
        indicator_summary=indicator_summary,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
    )


# ── Case-Scoped Assessment Endpoints ────────────────────────────────


@router.get("/cases/{case_id}/assessments", response_model=dict[str, Any])
async def list_case_assessments(
    case_id: uuid.UUID,
    template_key: str | None = Query(None, description="Filter by template key"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_READ)),
):
    """List all assessments recorded on a specific case file with pagination and filters."""
    service = AssessmentService(db)
    items, total = await service.list_case_assessments(
        case_id=case_id,
        current_user=user,
        template_key=template_key,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    data = []
    for a in items:
        data.append(
            AssessmentResponse(
                id=a.id,
                case_id=a.case_id,
                case_number=None,
                person_id=a.person_id,
                person_name=f"{a.person.first_name} {a.person.last_name}" if a.person else None,
                client_id=a.client_id,
                family_id=a.family_id,
                family_name=a.family.family_name if a.family else None,
                household_id=a.household_id,
                template_id=a.template_id,
                template_key=a.template.key if a.template else None,
                template_name=a.template.name if a.template else None,
                template_category=a.template.category if a.template else None,
                template_version_id=a.template_version_id,
                version_number=a.template_version.version_number if a.template_version else None,
                assessment_number=a.assessment_number,
                title=a.title,
                status=a.status,
                determination=a.determination,
                determination_notes=a.determination_notes,
                conducted_by=a.conducted_by,
                conducted_by_name=a.conductor.full_name or a.conductor.email if a.conductor else None,
                conducted_at=a.conducted_at,
                completed_at=a.completed_at,
                completed_by=a.completed_by,
                locked_at=a.locked_at,
                locked_by=a.locked_by,
                is_locked=a.status == "LOCKED",
                summary=a.summary,
                metadata_=a.metadata_,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
    return {"items": data, "total": total, "limit": limit, "offset": offset}


@router.post(
    "/cases/{case_id}/assessments", response_model=AssessmentDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_assessment(
    case_id: uuid.UUID,
    payload: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_CREATE)),
):
    """Start a new assessment instance for a case file."""
    if payload.case_id != case_id:
        payload.case_id = case_id

    service = AssessmentService(db)
    assessment = await service.create_assessment(payload, current_user=user)
    await db.commit()
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


# ── Assessment Instance Operations ──────────────────────────────────


@router.get("/assessments/compare", response_model=AssessmentComparisonResponse)
async def compare_assessments(
    ids: str | None = Query(None, description="Comma-separated assessment UUIDs (e.g. ?ids=uuid1,uuid2)"),
    assessment_ids: list[str] | None = Query(
        None, description="List of assessment UUIDs (e.g. ?assessment_ids=uuid1&assessment_ids=uuid2)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_COMPARE)),
):
    """Compare question responses across multiple assessments of the same template over time."""
    raw_ids: list[str] = []
    if ids:
        raw_ids.extend([s.strip() for s in ids.split(",") if s.strip()])
    if assessment_ids:
        raw_ids.extend([s.strip() for s in assessment_ids if s.strip()])

    if not raw_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one assessment ID must be provided for comparison.",
        )

    parsed_ids: list[uuid.UUID] = []
    for r in raw_ids:
        try:
            parsed_ids.append(uuid.UUID(r))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid UUID: {r}") from None

    service = AssessmentService(db)
    return await service.compare_assessments(parsed_ids, current_user=user)


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_READ)),
):
    """Get full assessment structure, questions, answers, lock status, and indicator summary."""
    service = AssessmentService(db)
    assessment = await service.get_assessment_or_404(assessment_id, current_user=user)
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


@router.patch("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def update_assessment_metadata(
    assessment_id: uuid.UUID,
    payload: AssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_UPDATE)),
):
    """Update assessment title, conducted date, summary, or determination metadata."""
    service = AssessmentService(db)
    await service.update_assessment_metadata(assessment_id, payload, current_user=user)
    await db.commit()
    assessment = await service.get_assessment_or_404(assessment_id, current_user=user)
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


@router.put("/assessments/{assessment_id}/answers", response_model=AssessmentDetailResponse)
async def save_assessment_answers(
    assessment_id: uuid.UUID,
    payload: AssessmentAnswersSaveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_UPDATE)),
):
    """Save answers for questions in the assessment (moves DRAFT to IN_PROGRESS)."""
    service = AssessmentService(db)
    assessment = await service.save_answers(assessment_id, payload, current_user=user)
    await db.commit()
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentDetailResponse)
async def complete_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_COMPLETE)),
):
    """Validate all required fields and complete the assessment with final clinical determination."""
    service = AssessmentService(db)
    assessment = await service.complete_assessment(assessment_id, payload, current_user=user)
    await db.commit()
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


@router.post("/assessments/{assessment_id}/lock", response_model=AssessmentDetailResponse)
async def lock_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentLockRequest = AssessmentLockRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_LOCK)),
):
    """Permanently lock a completed assessment, making answers immutable."""
    service = AssessmentService(db)
    assessment = await service.lock_assessment(assessment_id, payload, current_user=user)
    await db.commit()
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


@router.post("/assessments/{assessment_id}/unlock", response_model=AssessmentDetailResponse)
async def unlock_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentUnlockRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_UNLOCK)),
):
    """Director / Supervisor unlock of a finalized assessment with mandatory justification."""
    service = AssessmentService(db)
    assessment = await service.unlock_assessment(assessment_id, payload, current_user=user)
    await db.commit()
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)


@router.post("/assessments/{assessment_id}/reassign", response_model=AssessmentDetailResponse)
async def reassign_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentReassignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permissions.ASSESSMENT_REASSIGN)),
):
    """Director reassignment of an assessment filed under the wrong case or family."""
    service = AssessmentService(db)
    assessment = await service.reassign_assessment(assessment_id, payload, current_user=user)
    await db.commit()
    summary = service._compute_indicator_summary(assessment)
    return _to_detail_response(assessment, indicator_summary=summary)
