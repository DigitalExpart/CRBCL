"""FastAPI router for Calendar and Scheduling endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["Calendar & Scheduling"])


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new calendar appointment or custom event."""
    service = CalendarService(db)
    event = await service.create_event(
        event_type=payload.event_type,
        title=payload.title,
        start_at=payload.start_at,
        end_at=payload.end_at,
        all_day=payload.all_day,
        timezone=payload.timezone,
        location=payload.location,
        description=payload.description,
        source_entity_type=payload.source_entity_type,
        source_entity_id=payload.source_entity_id,
        case_id=payload.case_id,
        person_id=payload.person_id,
        team_id=payload.team_id,
        assigned_user_id=payload.assigned_user_id,
        status_val=payload.status,
        recurrence_data=payload.recurrence.model_dump() if payload.recurrence else None,
        current_user=current_user,
    )
    await db.commit()
    full_event = await service.repo.get_by_id(event.id)
    return await service._format_and_sanitize_event(full_event, current_user)


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single calendar event details."""
    service = CalendarService(db)
    event = await service.repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")
    return await service._format_and_sanitize_event(event, current_user)


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: uuid.UUID,
    payload: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update calendar event properties."""
    service = CalendarService(db)
    update_data = payload.model_dump(exclude_unset=True)
    event = await service.repo.update(event_id, update_data, updated_by=current_user.id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")
    await db.commit()
    return await service._format_and_sanitize_event(event, current_user)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a calendar event."""
    service = CalendarService(db)
    success = await service.repo.delete(event_id, deleted_by=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")
    await db.commit()


@router.get("/my-schedule", response_model=list[CalendarEventResponse])
async def get_my_schedule(
    start_at: datetime = Query(..., description="Query window start (UTC)"),
    end_at: datetime = Query(..., description="Query window end (UTC)"),
    event_types: list[str] | None = Query(None, description="Optional filter by event types"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's personal authorized schedule with case-restriction privacy masking."""
    service = CalendarService(db)
    return await service.get_my_schedule(
        current_user=current_user,
        start_at=start_at,
        end_at=end_at,
        event_types=event_types,
    )


@router.get("/team-schedule", response_model=list[CalendarEventResponse])
async def get_team_schedule(
    start_at: datetime = Query(..., description="Query window start (UTC)"),
    end_at: datetime = Query(..., description="Query window end (UTC)"),
    team_id: uuid.UUID | None = Query(None, description="Optional team scope"),
    worker_ids: list[uuid.UUID] | None = Query(None, description="Optional worker filter"),
    event_types: list[str] | None = Query(None, description="Optional filter by event types"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor and Director multi-worker team schedule with privacy masking."""
    service = CalendarService(db)
    return await service.get_team_schedule(
        current_user=current_user,
        start_at=start_at,
        end_at=end_at,
        team_id=team_id,
        worker_ids=worker_ids,
        event_types=event_types,
    )
