"""FastAPI Endpoints for Court Events and Legal Proceedings."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement import (
    CourtEventCreate,
    CourtEventListResponse,
    CourtEventResponse,
    CourtEventUpdate,
)
from app.services.court_event_service import CourtEventService

router = APIRouter(tags=["Court Events & Legal Proceedings"])


@router.post(
    "/cases/{case_id}/court-events",
    response_model=CourtEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_court_event(
    case_id: uuid.UUID,
    payload: CourtEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourtEventResponse:
    service = CourtEventService(db)
    event = await service.create_court_event(current_user, case_id, payload)
    return CourtEventResponse.model_validate(event)


@router.get("/cases/{case_id}/court-events", response_model=CourtEventListResponse)
async def list_case_court_events(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> CourtEventListResponse:
    service = CourtEventService(db)
    items, total = await service.list_court_events_by_case(current_user, case_id, page=page, page_size=page_size)
    return CourtEventListResponse(
        items=[CourtEventResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/court-events/{event_id}", response_model=CourtEventResponse)
async def get_court_event(
    event_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourtEventResponse:
    service = CourtEventService(db)
    event = await service.get_court_event(current_user, event_id)
    return CourtEventResponse.model_validate(event)


@router.patch("/court-events/{event_id}", response_model=CourtEventResponse)
async def update_court_event(
    event_id: uuid.UUID,
    payload: CourtEventUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourtEventResponse:
    service = CourtEventService(db)
    event = await service.update_court_event(current_user, event_id, payload)
    return CourtEventResponse.model_validate(event)
