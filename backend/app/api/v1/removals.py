"""FastAPI Endpoints for Child Removal Episodes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement import (
    RemovalEpisodeCreate,
    RemovalEpisodeListResponse,
    RemovalEpisodeResponse,
    RemovalEpisodeUpdate,
)
from app.services.removal_service import RemovalService

router = APIRouter(tags=["Child Removal Episodes"])


@router.post(
    "/cases/{case_id}/removals",
    response_model=RemovalEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_removal_episode(
    case_id: uuid.UUID,
    payload: RemovalEpisodeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RemovalEpisodeResponse:
    service = RemovalService(db)
    removal = await service.create_removal_episode(current_user, case_id, payload)
    return RemovalEpisodeResponse.model_validate(removal)


@router.get("/cases/{case_id}/removals", response_model=RemovalEpisodeListResponse)
async def list_case_removals(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> RemovalEpisodeListResponse:
    service = RemovalService(db)
    items, total = await service.list_removal_episodes_by_case(
        current_user, case_id, page=page, page_size=page_size
    )
    return RemovalEpisodeListResponse(
        items=[RemovalEpisodeResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/removals/{removal_id}", response_model=RemovalEpisodeResponse)
async def get_removal_episode(
    removal_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RemovalEpisodeResponse:
    service = RemovalService(db)
    removal = await service.get_removal_episode(current_user, removal_id)
    return RemovalEpisodeResponse.model_validate(removal)


@router.patch("/removals/{removal_id}", response_model=RemovalEpisodeResponse)
async def update_removal_episode(
    removal_id: uuid.UUID,
    payload: RemovalEpisodeUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RemovalEpisodeResponse:
    service = RemovalService(db)
    removal = await service.update_removal_episode(current_user, removal_id, payload)
    return RemovalEpisodeResponse.model_validate(removal)
