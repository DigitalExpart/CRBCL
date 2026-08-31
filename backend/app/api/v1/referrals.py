"""Referral, Screening, Decision, and Approval endpoints."""

from __future__ import annotations

import math
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.repositories.referral_repo import ReferralRepository
from app.schemas.referral import (
    IntakeDecisionApprove,
    IntakeDecisionReturn,
    IntakeDecisionSubmit,
    ReferralConcernCreate,
    ReferralConcernResponse,
    ReferralCreate,
    ReferralDetailResponse,
    ReferralIncidentCreate,
    ReferralIncidentResponse,
    ReferralLinkCreate,
    ReferralLinkResponse,
    ReferralListResponse,
    ReferralPersonCreate,
    ReferralPersonResponse,
    ReferralReporterCreate,
    ReferralReporterResponse,
    ReferralResponse,
    ReferralUpdate,
)
from app.services.intake_approval_service import IntakeApprovalService
from app.services.intake_decision_service import IntakeDecisionService
from app.services.referral_history_service import ReferralHistoryService
from app.services.referral_service import ReferralService

router = APIRouter(prefix="/referrals", tags=["Intake & Referrals"])


# ── Referral Core Endpoints ───────────────────────────────────

@router.get("", response_model=ReferralListResponse)
async def list_referrals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    concern_type: str | None = None,
    worker_id: uuid.UUID | None = None,
    team_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(require_permission(Permissions.INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List referrals with multi-facet filtering and server-side pagination."""
    repo = ReferralRepository(db)
    items, total = await repo.list_referrals(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        priority=priority,
        assigned_worker_id=worker_id,
        assigned_team_id=team_id,
        concern_type=concern_type,
        date_from=date_from,
        date_to=date_to,
    )

    responses = []
    for r in items:
        children_count = sum(1 for p in r.people if p.role == "child")
        primary_c = next((c.concern_type for c in r.concerns if c.is_primary), None)
        if not primary_c and r.concerns:
            primary_c = r.concerns[0].concern_type

        responses.append(
            ReferralResponse(
                id=r.id,
                referral_number=r.referral_number,
                status=r.status,
                received_date=r.received_date,
                received_time=r.received_time,
                received_method=r.received_method,
                community=r.community,
                priority=r.priority,
                risk_level=r.risk_level,
                summary=r.summary,
                immediate_safety_concerns=r.immediate_safety_concerns,
                law_enforcement_involved=r.law_enforcement_involved,
                law_enforcement_file_number=r.law_enforcement_file_number,
                law_enforcement_officer_info=r.law_enforcement_officer_info,
                assigned_worker_id=r.assigned_worker_id,
                assigned_worker_name=r.assigned_worker_name,
                assigned_team_id=r.assigned_team_id,
                origin_agency=r.origin_agency,
                notes=r.notes,
                version=r.version,
                created_at=r.created_at,
                updated_at=r.updated_at,
                people_count=len(r.people),
                children_count=children_count,
                primary_concern=primary_c,
            )
        )

    return ReferralListResponse(
        items=responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.post("", response_model=ReferralResponse, status_code=status.HTTP_201_CREATED)
async def create_referral(
    payload: ReferralCreate,
    user: User = Depends(require_permission(Permissions.INTAKE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new intake referral record."""
    service = ReferralService(db)
    created = await service.create_referral(payload.model_dump(), created_by=user.id)
    await db.commit()

    detail = await service.get_referral_detail(created.id, can_read_reporter=True)
    return detail


@router.get("/approvals/queue", response_model=ReferralListResponse)
async def list_supervisor_approval_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    team_id: uuid.UUID | None = None,
    user: User = Depends(require_permission(Permissions.INTAKE_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor queue for reviewing pending referrals."""
    repo = ReferralRepository(db)
    items, total = await repo.list_pending_approvals(page=page, page_size=page_size, team_id=team_id)

    responses = []
    for r in items:
        children_count = sum(1 for p in r.people if p.role == "child")
        primary_c = next((c.concern_type for c in r.concerns if c.is_primary), None)
        responses.append(
            ReferralResponse(
                id=r.id,
                referral_number=r.referral_number,
                status=r.status,
                received_date=r.received_date,
                received_time=r.received_time,
                received_method=r.received_method,
                community=r.community,
                priority=r.priority,
                risk_level=r.risk_level,
                summary=r.summary,
                immediate_safety_concerns=r.immediate_safety_concerns,
                law_enforcement_involved=r.law_enforcement_involved,
                assigned_worker_id=r.assigned_worker_id,
                assigned_worker_name=r.assigned_worker_name,
                assigned_team_id=r.assigned_team_id,
                version=r.version,
                created_at=r.created_at,
                updated_at=r.updated_at,
                people_count=len(r.people),
                children_count=children_count,
                primary_concern=primary_c,
            )
        )

    return ReferralListResponse(
        items=responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/{referral_id}", response_model=ReferralDetailResponse)
async def get_referral_detail(
    referral_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.INTAKE_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get complete 360° referral detail with backend reporter privacy enforcement."""
    perm_service = PermissionService(db)
    can_read_reporter = await perm_service.user_has_permission(user.id, Permissions.INTAKE_REPORTER_READ)

    service = ReferralService(db)
    detail = await service.get_referral_detail(referral_id, can_read_reporter=can_read_reporter)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REFERRAL_NOT_FOUND", "message": f"Referral {referral_id} not found"}},
        )
    return detail


@router.patch("/{referral_id}", response_model=ReferralDetailResponse)
async def update_referral_metadata(
    referral_id: uuid.UUID,
    payload: ReferralUpdate,
    user: User = Depends(require_permission(Permissions.INTAKE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Update referral metadata (status cannot be mutated arbitrarily via PATCH)."""
    service = ReferralService(db)
    try:
        await service.update_referral(
            referral_id, payload.model_dump(exclude_unset=True), user_id=user.id
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": {"message": str(e)}}) from e

    perm_service = PermissionService(db)
    can_read_reporter = await perm_service.user_has_permission(user.id, Permissions.INTAKE_REPORTER_READ)
    return await service.get_referral_detail(referral_id, can_read_reporter=can_read_reporter)


# ── Involved People Endpoints ─────────────────────────────────

@router.post("/{referral_id}/people", response_model=ReferralPersonResponse, status_code=status.HTTP_201_CREATED)
async def add_person_to_referral(
    referral_id: uuid.UUID,
    payload: ReferralPersonCreate,
    user: User = Depends(require_permission(Permissions.INTAKE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Associate a canonical person to the referral with role context."""
    repo = ReferralRepository(db)
    ref = await repo.get_by_id(referral_id)
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    rp = await repo.add_person(
        referral_id=referral_id,
        person_id=payload.person_id,
        role=payload.role,
        relationship_to_child=payload.relationship_to_child,
        is_primary_caregiver=payload.is_primary_caregiver,
        is_subject_of_concern=payload.is_subject_of_concern,
        notes=payload.notes,
    )
    await db.commit()
    return ReferralPersonResponse.model_validate(rp)


@router.delete("/{referral_id}/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_person_from_referral(
    referral_id: uuid.UUID,
    person_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.INTAKE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Remove person association from referral."""
    repo = ReferralRepository(db)
    removed = await repo.remove_person(referral_id, person_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person association not found")
    await db.commit()


# ── Confidential Reporter Endpoints ───────────────────────────

@router.get("/{referral_id}/reporter", response_model=ReferralReporterResponse)
async def get_referral_reporter(
    referral_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.INTAKE_REPORTER_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve confidential reporter details (strictly protected)."""
    repo = ReferralRepository(db)
    ref = await repo.get_by_id(referral_id)
    if not ref or not ref.reporter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporter not found")
    return ReferralReporterResponse.model_validate(ref.reporter)


@router.put("/{referral_id}/reporter", response_model=ReferralReporterResponse)
async def save_referral_reporter(
    referral_id: uuid.UUID,
    payload: ReferralReporterCreate,
    user: User = Depends(require_permission(Permissions.INTAKE_REPORTER_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Save or update confidential reporter details."""
    repo = ReferralRepository(db)
    ref = await repo.get_by_id(referral_id)
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    rep = await repo.save_reporter(referral_id, payload.model_dump())
    await db.commit()
    return ReferralReporterResponse.model_validate(rep)


# ── Incidents & Concerns Endpoints ────────────────────────────

@router.post("/{referral_id}/incidents", response_model=ReferralIncidentResponse, status_code=status.HTTP_201_CREATED)
async def add_incident(
    referral_id: uuid.UUID,
    payload: ReferralIncidentCreate,
    user: User = Depends(require_permission(Permissions.INTAKE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ReferralRepository(db)
    ref = await repo.get_by_id(referral_id)
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    inc = await repo.add_incident(referral_id, payload.model_dump())
    await db.commit()
    return ReferralIncidentResponse.model_validate(inc)


@router.post("/{referral_id}/concerns", response_model=ReferralConcernResponse, status_code=status.HTTP_201_CREATED)
async def add_concern(
    referral_id: uuid.UUID,
    payload: ReferralConcernCreate,
    user: User = Depends(require_permission(Permissions.INTAKE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ReferralRepository(db)
    ref = await repo.get_by_id(referral_id)
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    concern = await repo.add_concern(referral_id, payload.model_dump())
    await db.commit()
    return ReferralConcernResponse.model_validate(concern)


@router.delete("/{referral_id}/concerns/{concern_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concern(
    referral_id: uuid.UUID,
    concern_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.INTAKE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ReferralRepository(db)
    deleted = await repo.remove_concern(referral_id, concern_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concern not found")
    await db.commit()


# ── Prior History Discovery ───────────────────────────────────

@router.get("/{referral_id}/history")
async def get_prior_history(
    referral_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.INTAKE_HISTORY_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Discover prior intakes and cases for all persons on the referral."""
    service = ReferralHistoryService(db)
    return await service.get_prior_history_for_referral(referral_id, user_id=user.id)


# ── Cross-Referral Links ──────────────────────────────────────

@router.get("/{referral_id}/links", response_model=list[ReferralLinkResponse])
async def get_referral_links(
    referral_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.INTAKE_LINK_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = ReferralRepository(db)
    ref = await repo.get_by_id(referral_id)
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
    return [
        ReferralLinkResponse(
            id=lk.id,
            source_referral_id=lk.source_referral_id,
            target_referral_id=lk.target_referral_id,
            target_referral_number=lk.target_referral.referral_number if lk.target_referral else None,
            target_referral_status=lk.target_referral.status if lk.target_referral else None,
            link_type=lk.link_type,
            reason=lk.reason,
            created_at=lk.created_at,
        )
        for lk in ref.outgoing_links
    ]


@router.post("/{referral_id}/links", response_model=ReferralLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_referral_link(
    referral_id: uuid.UUID,
    payload: ReferralLinkCreate,
    user: User = Depends(require_permission(Permissions.INTAKE_LINK_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ReferralRepository(db)
    try:
        link = await repo.create_link(
            source_referral_id=referral_id,
            target_referral_id=payload.target_referral_id,
            link_type=payload.link_type,
            reason=payload.reason,
            created_by=user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return ReferralLinkResponse(
        id=link.id,
        source_referral_id=link.source_referral_id,
        target_referral_id=link.target_referral_id,
        link_type=link.link_type,
        reason=link.reason,
        created_at=link.created_at,
    )


# ── Decision & Workflow Actions ───────────────────────────────

@router.put("/{referral_id}/decision", response_model=ReferralDetailResponse)
async def save_decision_draft(
    referral_id: uuid.UUID,
    payload: IntakeDecisionSubmit,
    user: User = Depends(require_permission(Permissions.INTAKE_DECISION_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Save decision recommendation and per-child dispositions."""
    decision_service = IntakeDecisionService(db)
    await decision_service.save_decision(referral_id, payload, user_id=user.id)
    await db.commit()

    service = ReferralService(db)
    return await service.get_referral_detail(referral_id, can_read_reporter=True)


@router.post("/{referral_id}/submit", response_model=ReferralDetailResponse)
async def submit_referral_for_approval(
    referral_id: uuid.UUID,
    payload: IntakeDecisionSubmit,
    user: User = Depends(require_permission(Permissions.INTAKE_SUBMIT)),
    db: AsyncSession = Depends(get_db),
):
    """Worker submits intake referral with child dispositions for supervisor approval."""
    # 1. Save decision first
    decision_service = IntakeDecisionService(db)
    await decision_service.save_decision(referral_id, payload, user_id=user.id)

    # 2. Submit workflow
    approval_service = IntakeApprovalService(db)
    try:
        await approval_service.submit_for_approval(referral_id, user_id=user.id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": {"message": str(e)}}) from e

    service = ReferralService(db)
    return await service.get_referral_detail(referral_id, can_read_reporter=True)


@router.post("/{referral_id}/approve", response_model=ReferralDetailResponse)
async def approve_referral(
    referral_id: uuid.UUID,
    payload: IntakeDecisionApprove = IntakeDecisionApprove(),
    user: User = Depends(require_permission(Permissions.INTAKE_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor approves referral, triggering automated case and disposition routing."""
    approval_service = IntakeApprovalService(db)
    try:
        await approval_service.approve_referral(
            referral_id=referral_id,
            supervisor_id=user.id,
            supervisor_notes=payload.supervisor_notes,
            idempotency_key=payload.idempotency_key,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": {"message": str(e)}}) from e

    service = ReferralService(db)
    return await service.get_referral_detail(referral_id, can_read_reporter=True)


@router.post("/{referral_id}/return", response_model=ReferralDetailResponse)
async def return_referral(
    referral_id: uuid.UUID,
    payload: IntakeDecisionReturn,
    user: User = Depends(require_permission(Permissions.INTAKE_RETURN)),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor returns referral to worker with required comments."""
    approval_service = IntakeApprovalService(db)
    try:
        await approval_service.return_to_worker(
            referral_id=referral_id,
            supervisor_id=user.id,
            return_reason=payload.return_reason,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": {"message": str(e)}}) from e

    service = ReferralService(db)
    return await service.get_referral_detail(referral_id, can_read_reporter=True)
