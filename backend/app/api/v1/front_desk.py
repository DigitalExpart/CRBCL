"""API router for Front Desk Public Intake & Ingestion Pipeline."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.front_desk import FrontDeskSubmission
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.front_desk import (
    ConversionLinkResponse,
    CreateReferralFromSubmissionRequest,
    DepartmentActionRequest,
    DuplicateCandidateResponse,
    FrontDeskStatsResponse,
    FrontDeskSubmissionManualCreate,
    FrontDeskSubmissionResponse,
    FrontDeskSubmissionReviewRequest,
    FrontDeskSubmissionRouteRequest,
    GenericConversionRequest,
    GoogleFormIngestRequest,
    RoutingHistoryResponse,
)
from app.services.front_desk_service import FrontDeskService

router = APIRouter(prefix="/front-desk", tags=["Front Desk"])


def _build_submission_response(sub: FrontDeskSubmission) -> FrontDeskSubmissionResponse:
    return FrontDeskSubmissionResponse(
        id=sub.id,
        submission_number=sub.submission_number,
        external_response_id=sub.external_response_id,
        source=sub.source,
        status=sub.status,
        urgency=sub.urgency,
        destination_department=sub.destination_department,
        destination_team_id=sub.destination_team_id,
        submitter_name=sub.submitter_name,
        submitter_email=sub.submitter_email,
        submitter_phone=sub.submitter_phone,
        submitter_relationship=sub.submitter_relationship,
        inquiry_type=sub.inquiry_type,
        summary=sub.summary,
        details=sub.details,
        payload_raw=sub.payload_raw or {},
        received_at=sub.received_at,
        front_desk_worker_id=sub.front_desk_worker_id,
        front_desk_worker_name=sub.front_desk_worker.full_name if sub.front_desk_worker else None,
        front_desk_notes=sub.front_desk_notes,
        department_worker_id=sub.department_worker_id,
        department_worker_name=sub.department_worker.full_name if sub.department_worker else None,
        department_notes=sub.department_notes,
        resulting_referral_id=sub.resulting_referral_id,
        resulting_referral_number=(
            sub.resulting_referral.referral_number if sub.resulting_referral else None
        ),
        routing_history=[
            RoutingHistoryResponse(
                id=h.id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                previous_destination=h.previous_destination,
                new_destination=h.new_destination,
                changed_by_id=h.changed_by_id,
                changed_by_name=h.changed_by.full_name if h.changed_by else None,
                changed_at=h.changed_at,
                reason_note=h.reason_note,
            )
            for h in (sub.routing_history or [])
        ],
        conversion_links=[
            ConversionLinkResponse(
                id=c.id,
                downstream_entity_type=c.downstream_entity_type,
                downstream_entity_id=c.downstream_entity_id,
                downstream_entity_reference=c.downstream_entity_reference,
                created_by_id=c.created_by_id,
                created_by_name=c.created_by.full_name if c.created_by else None,
                created_at=c.created_at,
                notes=c.notes,
            )
            for c in (sub.conversion_links or [])
        ],
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


@router.post(
    "/ingest/google-form",
    summary="Ingest Google Form webhook submission",
)
async def ingest_google_form(
    payload: GoogleFormIngestRequest,
    response: Response,
    request: Request,
    x_crbcl_webhook_secret: str | None = Header(default=None, alias="X-CRBCL-Webhook-Secret"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Public ingestion webhook for Google Form / external webhooks.

    Secured via constant-time shared webhook secret header.
    Guarantees idempotency on response_id, payload immutability, zero Person/Client/Family/Case creation.
    """
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 2 * 1024 * 1024:  # 2MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload size exceeds 2MB limit",
        )

    service = FrontDeskService(db)
    submission, is_new = await service.ingest_google_form(payload, secret_token=x_crbcl_webhook_secret)

    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return {
        "status": submission.status,
        "submission_id": submission.id,
        "submission_number": submission.submission_number,
        "received_at": submission.received_at.isoformat(),
        "is_duplicate": not is_new,
    }


@router.get("/stats", response_model=FrontDeskStatsResponse)
async def get_front_desk_stats(
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve queue counts and department routing breakdown statistics."""
    service = FrontDeskService(db)
    return await service.get_stats()


@router.get("/submissions", response_model=PaginatedResponse[FrontDeskSubmissionResponse])
async def list_submissions(
    status_filter: str | None = Query(default=None, alias="status"),
    department_filter: str | None = Query(default=None, alias="department"),
    query: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List Front Desk submissions queue with filters."""
    service = FrontDeskService(db)
    items, total = await service.list_submissions(
        status_filter=status_filter,
        department_filter=department_filter,
        query=query,
        offset=offset,
        limit=limit,
    )

    return PaginatedResponse[FrontDeskSubmissionResponse](
        items=[_build_submission_response(s) for s in items],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get("/department-queue", response_model=PaginatedResponse[FrontDeskSubmissionResponse])
async def list_department_queue(
    department: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Receiving department queue for authorized staff."""
    target_department = department or user.department
    service = FrontDeskService(db)
    items, total = await service.list_submissions(
        status_filter=status_filter,
        department_filter=target_department,
        offset=offset,
        limit=limit,
    )
    return PaginatedResponse[FrontDeskSubmissionResponse](
        items=[_build_submission_response(s) for s in items],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.post(
    "/submissions/manual",
    response_model=FrontDeskSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_submission(
    payload: FrontDeskSubmissionManualCreate,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_TRIAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Record a walk-in, phone call, or counter inquiry directly at the front desk."""
    service = FrontDeskService(db)
    submission = await service.create_manual_submission(payload, user_id=user.id)
    return _build_submission_response(submission)


@router.get("/submissions/{submission_id}", response_model=FrontDeskSubmissionResponse)
async def get_submission(
    submission_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get single submission details including raw payload, routing history, and downstream links."""
    service = FrontDeskService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Front Desk submission not found",
        )
    return _build_submission_response(submission)


@router.patch("/submissions/{submission_id}/review", response_model=FrontDeskSubmissionResponse)
async def review_submission(
    submission_id: uuid.UUID,
    payload: FrontDeskSubmissionReviewRequest,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_TRIAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Front Desk marks submission FRONT_DESK_REVIEW, DUPLICATE, OUT_OF_SCOPE, SPAM, or CLOSED."""
    service = FrontDeskService(db)
    updated = await service.review_submission_by_front_desk(
        submission_id=submission_id,
        user_id=user.id,
        new_status=payload.status,
        notes=payload.notes,
    )
    return _build_submission_response(updated)


@router.post("/submissions/{submission_id}/route", response_model=FrontDeskSubmissionResponse)
async def route_submission(
    submission_id: uuid.UUID,
    payload: FrontDeskSubmissionRouteRequest,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_ROUTE)),
    db: AsyncSession = Depends(get_db),
):
    """Front Desk routes submission to destination department/team with urgency and rationale."""
    service = FrontDeskService(db)
    routed = await service.route_submission(
        submission_id=submission_id,
        user_id=user.id,
        route_req=payload,
    )
    return _build_submission_response(routed)


@router.patch("/submissions/{submission_id}/department-action", response_model=FrontDeskSubmissionResponse)
async def department_action(
    submission_id: uuid.UUID,
    payload: DepartmentActionRequest,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_NOTE)),
    db: AsyncSession = Depends(get_db),
):
    """Receiving department staff reviews, accepts, returns to Front Desk, or marks duplicate/out of scope."""
    service = FrontDeskService(db)
    updated = await service.department_action(
        submission_id=submission_id,
        user_id=user.id,
        action=payload.action,
        notes=payload.notes,
    )
    return _build_submission_response(updated)


@router.get("/submissions/{submission_id}/duplicates", response_model=list[DuplicateCandidateResponse])
async def check_duplicates(
    submission_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Search existing Person / Client / Family records before canonical creation. Creates zero records."""
    service = FrontDeskService(db)
    return await service.check_duplicates(submission_id)


@router.post("/submissions/{submission_id}/convert-to-referral", response_model=dict[str, Any])
async def convert_to_referral(
    submission_id: uuid.UUID,
    payload: CreateReferralFromSubmissionRequest,
    user: User = Depends(require_permission(Permissions.INTAKE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Authorized Protection/Intake staff creates formal CRBCL Referral/Intake."""
    service = FrontDeskService(db)
    sub, referral = await service.convert_to_referral(
        submission_id=submission_id,
        user_id=user.id,
        req=payload,
    )
    return {
        "status": "CONVERTED",
        "submission_id": sub.id,
        "submission_number": sub.submission_number,
        "referral_id": referral.id,
        "referral_number": referral.referral_number,
    }


@router.post("/submissions/{submission_id}/convert-generic", response_model=ConversionLinkResponse)
async def convert_generic(
    submission_id: uuid.UUID,
    payload: GenericConversionRequest,
    user: User = Depends(require_permission(Permissions.PUBLIC_INTAKE_NOTE)),
    db: AsyncSession = Depends(get_db),
):
    """Create generic downstream linkage connecting public submission to any domain record."""
    service = FrontDeskService(db)
    link = await service.link_generic_conversion(
        submission_id=submission_id,
        user_id=user.id,
        req=payload,
    )
    return ConversionLinkResponse.model_validate(link)
