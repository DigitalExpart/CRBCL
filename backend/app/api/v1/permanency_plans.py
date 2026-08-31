"""FastAPI Endpoints for Permanency Plans and Family Visitation Plans."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement import (
    PermanencyPlanCreate,
    PermanencyPlanListResponse,
    PermanencyPlanResponse,
    PermanencyPlanUpdate,
    VisitationPlanCreate,
    VisitationPlanListResponse,
    VisitationPlanResponse,
    VisitationPlanUpdate,
)
from app.services.permanency_service import PermanencyService

router = APIRouter(tags=["Permanency & Visitation Plans"])


# ── Permanency Plans ─────────────────────────────────────────────────
@router.post(
    "/cases/{case_id}/permanency-plans",
    response_model=PermanencyPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permanency_plan(
    case_id: uuid.UUID,
    payload: PermanencyPlanCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PermanencyPlanResponse:
    service = PermanencyService(db)
    plan = await service.create_permanency_plan(current_user, case_id, payload)
    return PermanencyPlanResponse.model_validate(plan)


@router.get("/cases/{case_id}/permanency-plans", response_model=PermanencyPlanListResponse)
async def list_case_permanency_plans(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PermanencyPlanListResponse:
    service = PermanencyService(db)
    items, total = await service.list_permanency_plans_by_case(
        current_user, case_id, page=page, page_size=page_size
    )
    return PermanencyPlanListResponse(
        items=[PermanencyPlanResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/permanency-plans/{plan_id}", response_model=PermanencyPlanResponse)
async def get_permanency_plan(
    plan_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PermanencyPlanResponse:
    service = PermanencyService(db)
    plan = await service.get_permanency_plan(current_user, plan_id)
    return PermanencyPlanResponse.model_validate(plan)


@router.patch("/permanency-plans/{plan_id}", response_model=PermanencyPlanResponse)
async def update_permanency_plan(
    plan_id: uuid.UUID,
    payload: PermanencyPlanUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PermanencyPlanResponse:
    service = PermanencyService(db)
    plan = await service.update_permanency_plan(current_user, plan_id, payload)
    return PermanencyPlanResponse.model_validate(plan)


# ── Visitation Plans ─────────────────────────────────────────────────
@router.post(
    "/cases/{case_id}/visitation-plans",
    response_model=VisitationPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_visitation_plan(
    case_id: uuid.UUID,
    payload: VisitationPlanCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitationPlanResponse:
    service = PermanencyService(db)
    plan = await service.create_visitation_plan(current_user, case_id, payload)
    return VisitationPlanResponse.model_validate(plan)


@router.get("/cases/{case_id}/visitation-plans", response_model=VisitationPlanListResponse)
async def list_case_visitation_plans(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> VisitationPlanListResponse:
    service = PermanencyService(db)
    items, total = await service.list_visitation_plans_by_case(
        current_user, case_id, page=page, page_size=page_size
    )
    return VisitationPlanListResponse(
        items=[VisitationPlanResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/visitation-plans/{plan_id}", response_model=VisitationPlanResponse)
async def get_visitation_plan(
    plan_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitationPlanResponse:
    service = PermanencyService(db)
    plan = await service.get_visitation_plan(current_user, plan_id)
    return VisitationPlanResponse.model_validate(plan)


@router.patch("/visitation-plans/{plan_id}", response_model=VisitationPlanResponse)
async def update_visitation_plan(
    plan_id: uuid.UUID,
    payload: VisitationPlanUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitationPlanResponse:
    service = PermanencyService(db)
    plan = await service.update_visitation_plan(current_user, plan_id, payload)
    return VisitationPlanResponse.model_validate(plan)
