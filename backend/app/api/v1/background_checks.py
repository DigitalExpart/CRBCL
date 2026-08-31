"""FastAPI Endpoints for Background Checks and Placement Adjudication."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement import (
    BackgroundCheckAdjudicate,
    BackgroundCheckCreate,
    BackgroundCheckListResponse,
    BackgroundCheckResponse,
    BackgroundCheckUpdate,
)
from app.services.background_check_service import BackgroundCheckService

router = APIRouter(tags=["Background Checks"])


@router.post(
    "/background-checks",
    response_model=BackgroundCheckResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_background_check(
    payload: BackgroundCheckCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackgroundCheckResponse:
    service = BackgroundCheckService(db)
    check = await service.create_background_check(current_user, payload)
    return BackgroundCheckResponse.model_validate(check)


@router.get("/background-checks", response_model=BackgroundCheckListResponse)
async def list_background_checks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_type: str | None = Query(None),
    subject_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    check_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> BackgroundCheckListResponse:
    service = BackgroundCheckService(db)
    items, total = await service.list_background_checks(
        current_user,
        subject_type=subject_type,
        subject_id=subject_id,
        status_filter=status_filter,
        check_type=check_type,
        page=page,
        page_size=page_size,
    )
    return BackgroundCheckListResponse(
        items=[BackgroundCheckResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/background-checks/{check_id}", response_model=BackgroundCheckResponse)
async def get_background_check(
    check_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackgroundCheckResponse:
    service = BackgroundCheckService(db)
    check = await service.get_background_check(current_user, check_id)
    return BackgroundCheckResponse.model_validate(check)


@router.patch("/background-checks/{check_id}", response_model=BackgroundCheckResponse)
async def update_background_check(
    check_id: uuid.UUID,
    payload: BackgroundCheckUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackgroundCheckResponse:
    service = BackgroundCheckService(db)
    check = await service.update_background_check(current_user, check_id, payload)
    return BackgroundCheckResponse.model_validate(check)


@router.post("/background-checks/{check_id}/adjudicate", response_model=BackgroundCheckResponse)
async def adjudicate_background_check(
    check_id: uuid.UUID,
    payload: BackgroundCheckAdjudicate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackgroundCheckResponse:
    service = BackgroundCheckService(db)
    check = await service.adjudicate_background_check(current_user, check_id, payload)
    return BackgroundCheckResponse.model_validate(check)
