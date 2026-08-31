"""FastAPI Endpoints for Active Efforts."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement import (
    ActiveEffortCreate,
    ActiveEffortListResponse,
    ActiveEffortResponse,
    ActiveEffortUpdate,
)
from app.services.active_effort_service import ActiveEffortService

router = APIRouter(tags=["Active Efforts"])


@router.post(
    "/cases/{case_id}/active-efforts",
    response_model=ActiveEffortResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_active_effort(
    case_id: uuid.UUID,
    payload: ActiveEffortCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActiveEffortResponse:
    service = ActiveEffortService(db)
    effort = await service.create_active_effort(current_user, case_id, payload)
    return ActiveEffortResponse.model_validate(effort)


@router.get("/cases/{case_id}/active-efforts", response_model=ActiveEffortListResponse)
async def list_case_active_efforts(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    outcome: str | None = Query(None),
    effort_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> ActiveEffortListResponse:
    service = ActiveEffortService(db)
    items, total = await service.list_active_efforts_by_case(
        current_user,
        case_id,
        outcome=outcome,
        effort_type=effort_type,
        page=page,
        page_size=page_size,
    )
    return ActiveEffortListResponse(
        items=[ActiveEffortResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/active-efforts/{effort_id}", response_model=ActiveEffortResponse)
async def get_active_effort(
    effort_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActiveEffortResponse:
    service = ActiveEffortService(db)
    effort = await service.get_active_effort(current_user, effort_id)
    return ActiveEffortResponse.model_validate(effort)


@router.patch("/active-efforts/{effort_id}", response_model=ActiveEffortResponse)
async def update_active_effort(
    effort_id: uuid.UUID,
    payload: ActiveEffortUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActiveEffortResponse:
    service = ActiveEffortService(db)
    effort = await service.update_active_effort(current_user, effort_id, payload)
    return ActiveEffortResponse.model_validate(effort)
