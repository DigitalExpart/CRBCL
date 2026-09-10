"""API endpoints for Resource Unit recruitment pipeline and dashboard metrics."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_any_permission, require_permission
from app.schemas.placement_home import PlacementHomeMemberRead
from app.schemas.resource_recruitment import (
    ApplicantRole,
    RecruitmentApplicantRead,
    RecruitmentCreate,
    RecruitmentHistoryRead,
    RecruitmentListItem,
    RecruitmentRead,
    RecruitmentState,
    RecruitmentStateTransition,
    RecruitmentUpdate,
    ResourceDashboardMetrics,
)
from app.services.resource_recruitment_service import ResourceRecruitmentService

router = APIRouter(prefix="/resource-recruitment", tags=["Resource Recruitment"])


def _serialize_recruitment(r) -> RecruitmentRead:
    applicants_out = []
    for a in r.applicants:
        if a.deleted_at is None:
            p_name = None
            if a.person:
                p_name = f"{a.person.first_name} {a.person.last_name}"
            applicants_out.append(
                RecruitmentApplicantRead(
                    id=a.id,
                    recruitment_id=a.recruitment_id,
                    person_id=a.person_id,
                    role=a.role if isinstance(a.role, ApplicantRole) else ApplicantRole(a.role),
                    snapshot=a.snapshot,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                    person_name=p_name,
                )
            )

    history_out = []
    for h in r.history:
        if h.deleted_at is None:
            u_name = None
            if h.changed_by:
                u_name = h.changed_by.display_name or h.changed_by.full_name or h.changed_by.email
            history_out.append(
                RecruitmentHistoryRead(
                    id=h.id,
                    recruitment_id=h.recruitment_id,
                    from_state=h.from_state if isinstance(h.from_state, RecruitmentState) else RecruitmentState(h.from_state),
                    to_state=h.to_state if isinstance(h.to_state, RecruitmentState) else RecruitmentState(h.to_state),
                    changed_at=h.changed_at,
                    changed_by_id=h.changed_by_id,
                    changed_by_name=u_name,
                    notes=h.notes,
                )
            )

    home_code = r.resource_home.home_code if r.resource_home else None
    home_name = r.resource_home.name if r.resource_home else None

    return RecruitmentRead(
        id=r.id,
        resource_home_id=r.resource_home_id,
        current_state=r.current_state if isinstance(r.current_state, RecruitmentState) else RecruitmentState(r.current_state),
        previous_state=r.previous_state if (r.previous_state is None or isinstance(r.previous_state, RecruitmentState)) else RecruitmentState(r.previous_state),
        notes=r.notes,
        metadata_=r.metadata_,
        created_at=r.created_at,
        updated_at=r.updated_at,
        applicants=applicants_out,
        history=history_out,
        resource_home_code=home_code,
        resource_home_name=home_name,
    )


# ── Dashboard Endpoint ─────────────────────────────────────────────
@router.get(
    "/dashboard",
    response_model=ResourceDashboardMetrics,
    summary="Get authoritative Resource Team dashboard operational metrics",
)
async def get_resource_dashboard(
    current_user: Annotated[User, Depends(require_permission(Permissions.RESOURCE_DASHBOARD_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResourceDashboardMetrics:
    service = ResourceRecruitmentService(db)
    return await service.get_dashboard_metrics(current_user=current_user)


# ── Recruitment Endpoints ──────────────────────────────────────────
@router.get(
    "",
    response_model=list[RecruitmentListItem],
    summary="List recruitment applications",
)
async def list_recruitments(
    current_user: Annotated[User, Depends(require_permission(Permissions.RESOURCE_RECRUITMENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    state: RecruitmentState | None = Query(None, description="Filter by recruitment stage"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[RecruitmentListItem]:
    service = ResourceRecruitmentService(db)
    records = await service.list_recruitments(state=state, limit=limit, offset=offset)

    items = []
    for r in records:
        primary_name = None
        for a in r.applicants:
            if a.role == ApplicantRole.PRIMARY_APPLICANT and a.person:
                primary_name = f"{a.person.first_name} {a.person.last_name}"
                break
        if not primary_name and r.applicants and r.applicants[0].person:
            primary_name = f"{r.applicants[0].person.first_name} {r.applicants[0].person.last_name}"

        items.append(
            RecruitmentListItem(
                id=r.id,
                current_state=r.current_state if isinstance(r.current_state, RecruitmentState) else RecruitmentState(r.current_state),
                previous_state=r.previous_state if (r.previous_state is None or isinstance(r.previous_state, RecruitmentState)) else RecruitmentState(r.previous_state),
                resource_home_id=r.resource_home_id,
                resource_home_code=r.resource_home.home_code if r.resource_home else None,
                resource_home_name=r.resource_home.name if r.resource_home else None,
                primary_applicant_name=primary_name,
                applicant_count=len([a for a in r.applicants if a.deleted_at is None]),
                created_at=r.created_at,
                updated_at=r.updated_at,
                notes=r.notes,
            )
        )
    return items


@router.post(
    "",
    response_model=RecruitmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recruitment inquiry or application",
)
async def create_recruitment(
    payload: RecruitmentCreate,
    current_user: Annotated[User, Depends(require_permission(Permissions.RESOURCE_RECRUITMENT_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruitmentRead:
    service = ResourceRecruitmentService(db)
    recruitment = await service.create_recruitment(payload, current_user.id)
    return _serialize_recruitment(recruitment)


@router.get(
    "/{recruitment_id}",
    response_model=RecruitmentRead,
    summary="Get recruitment application details with applicants and history",
)
async def get_recruitment_detail(
    recruitment_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission(Permissions.RESOURCE_RECRUITMENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruitmentRead:
    service = ResourceRecruitmentService(db)
    recruitment = await service.get_recruitment(recruitment_id)
    return _serialize_recruitment(recruitment)


@router.post(
    "/{recruitment_id}/transition",
    response_model=RecruitmentRead,
    summary="Perform a validated recruitment state transition",
)
async def transition_recruitment_state(
    recruitment_id: uuid.UUID,
    payload: RecruitmentStateTransition,
    current_user: Annotated[User, Depends(require_permission(Permissions.RESOURCE_RECRUITMENT_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruitmentRead:
    service = ResourceRecruitmentService(db)
    recruitment = await service.transition_state(recruitment_id, payload, current_user.id)
    return _serialize_recruitment(recruitment)


@router.patch(
    "/{recruitment_id}",
    response_model=RecruitmentRead,
    summary="Update recruitment notes or linked placement home",
)
async def update_recruitment(
    recruitment_id: uuid.UUID,
    payload: RecruitmentUpdate,
    current_user: Annotated[User, Depends(require_permission(Permissions.RESOURCE_RECRUITMENT_WRITE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruitmentRead:
    service = ResourceRecruitmentService(db)
    recruitment = await service.update_recruitment(recruitment_id, payload, current_user.id)
    return _serialize_recruitment(recruitment)


# ── Household Historical Membership Helper ─────────────────────────
@router.post(
    "/members/{member_id}/end",
    response_model=PlacementHomeMemberRead,
    summary="End an active household membership period while preserving the historical row",
)
async def end_household_membership(
    member_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(
            require_any_permission(
                Permissions.RESOURCE_HOME_WRITE,
                Permissions.PLACEMENT_HOME_MEMBER_MANAGE,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlacementHomeMemberRead:
    service = ResourceRecruitmentService(db)
    member = await service.end_household_membership(member_id, current_user.id)
    return PlacementHomeMemberRead.model_validate(member)
