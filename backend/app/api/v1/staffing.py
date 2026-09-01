"""FastAPI router for Staffing Facilitator endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.staffing import (
    StaffingAttendeeCreate,
    StaffingAttendeeResponse,
    StaffingCaseAdd,
    StaffingCaseBucketsResponse,
    StaffingCaseResponse,
    StaffingCaseUpdate,
    StaffingSessionCreate,
    StaffingSessionResponse,
    StaffingSessionUpdate,
)
from app.services.staffing_service import StaffingService

router = APIRouter(prefix="/staffing", tags=["Staffing Facilitator"])


@router.post("/sessions", response_model=StaffingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_staffing_session(
    payload: StaffingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new multi-disciplinary staffing conference session."""
    service = StaffingService(db)
    session = await service.create_session(
        session_date=payload.session_date,
        title=payload.title,
        facilitator_id=payload.facilitator_id,
        team_id=payload.team_id,
        cadence=payload.cadence,
        status_val=payload.status,
        location=payload.location,
        minutes=payload.minutes,
        attendee_ids=payload.attendee_ids,
        case_ids=payload.case_ids,
        current_user=current_user,
    )
    await db.commit()
    return await service.get_session(session.id, current_user)


@router.get("/sessions", response_model=dict)
async def list_staffing_sessions(
    status: str | None = Query(None),
    team_id: uuid.UUID | None = Query(None),
    facilitator_id: uuid.UUID | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List staffing sessions with pagination and filters."""
    service = StaffingService(db)
    items, total = await service.list_sessions(
        status_val=status,
        team_id=team_id,
        facilitator_id=facilitator_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        current_user=current_user,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/sessions/{session_id}", response_model=StaffingSessionResponse)
async def get_staffing_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get staffing session details including attendees and cases."""
    service = StaffingService(db)
    return await service.get_session(session_id, current_user)


@router.patch("/sessions/{session_id}", response_model=StaffingSessionResponse)
async def update_staffing_session(
    session_id: uuid.UUID,
    payload: StaffingSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update staffing session properties."""
    service = StaffingService(db)
    update_data = payload.model_dump(exclude_unset=True)
    res = await service.update_session(session_id, update_data, current_user)
    await db.commit()
    return res


@router.post("/sessions/{session_id}/attendees", response_model=StaffingAttendeeResponse, status_code=status.HTTP_201_CREATED)
async def add_session_attendee(
    session_id: uuid.UUID,
    payload: StaffingAttendeeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add or update an attendee on a staffing session."""
    service = StaffingService(db)
    attendee = await service.add_attendee(
        session_id=session_id,
        user_id=payload.user_id,
        status_val=payload.attendance_status,
        notes=payload.notes,
        current_user=current_user,
    )
    await db.commit()
    return StaffingAttendeeResponse(
        id=attendee.id,
        session_id=attendee.session_id,
        user_id=attendee.user_id,
        attendance_status=attendee.attendance_status,
        notes=attendee.notes,
        created_at=attendee.created_at,
        user_name=attendee.user.full_name if attendee.user else None,
        user_email=attendee.user.email if attendee.user else None,
    )


@router.post("/sessions/{session_id}/cases", response_model=StaffingCaseResponse, status_code=status.HTTP_201_CREATED)
async def add_session_case(
    session_id: uuid.UUID,
    payload: StaffingCaseAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a case to the staffing review roster."""
    service = StaffingService(db)
    sc = await service.add_case(
        session_id=session_id,
        case_id=payload.case_id,
        review_status=payload.review_status,
        discussion_summary=payload.discussion_summary,
        follow_up_required=payload.follow_up_required,
        follow_up_date=payload.follow_up_date,
        assigned_worker_id=payload.assigned_worker_id,
        current_user=current_user,
    )
    await db.commit()
    return StaffingCaseResponse(
        id=sc.id,
        session_id=sc.session_id,
        case_id=sc.case_id,
        review_status=sc.review_status,
        discussion_summary=sc.discussion_summary,
        follow_up_required=sc.follow_up_required,
        follow_up_date=sc.follow_up_date,
        assigned_worker_id=sc.assigned_worker_id,
        created_at=sc.created_at,
        case_number=sc.case.case_number if sc.case else None,
        case_title=sc.case.title if sc.case else None,
        assigned_worker_name=sc.assigned_worker.full_name if sc.assigned_worker else None,
    )


@router.patch("/sessions/{session_id}/cases/{case_id}", response_model=StaffingCaseResponse)
async def update_session_case_review(
    session_id: uuid.UUID,
    case_id: uuid.UUID,
    payload: StaffingCaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record case discussion review outcome and follow-up actions."""
    service = StaffingService(db)
    update_data = payload.model_dump(exclude_unset=True)
    sc = await service.update_case_review(session_id, case_id, update_data, current_user)
    await db.commit()
    return StaffingCaseResponse(
        id=sc.id,
        session_id=sc.session_id,
        case_id=sc.case_id,
        review_status=sc.review_status,
        discussion_summary=sc.discussion_summary,
        follow_up_required=sc.follow_up_required,
        follow_up_date=sc.follow_up_date,
        assigned_worker_id=sc.assigned_worker_id,
        created_at=sc.created_at,
        case_number=sc.case.case_number if sc.case else None,
        case_title=sc.case.title if sc.case else None,
        assigned_worker_name=sc.assigned_worker.full_name if sc.assigned_worker else None,
    )


@router.post("/sessions/{session_id}/complete", response_model=StaffingSessionResponse)
async def complete_staffing_session(
    session_id: uuid.UUID,
    minutes: str | None = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Command endpoint completing a staffing session, finalizing reviews and updating derived last-staffed status."""
    service = StaffingService(db)
    res = await service.complete_session(session_id, minutes=minutes, current_user=current_user)
    await db.commit()
    return res


@router.get("/case-buckets", response_model=StaffingCaseBucketsResponse)
async def get_staffing_case_buckets(
    team_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve automated server-side case triage buckets (Not staffed 90+ days, Open 12+ months, High Risk, Missing notes)."""
    service = StaffingService(db)
    return await service.get_case_buckets(team_id=team_id, current_user=current_user)
