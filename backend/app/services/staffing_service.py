"""Staffing domain service for sessions, attendance, case review workflows, triage buckets, and calendar sync."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.staffing import StaffingAttendee, StaffingCase, StaffingSession
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.calendar_repo import CalendarRepo
from app.repositories.staffing_repo import StaffingRepo
from app.schemas.staffing import (
    StaffingAttendeeResponse,
    StaffingCaseBucketsResponse,
    StaffingCaseResponse,
    StaffingSessionResponse,
)

logger = logging.getLogger("crbcl.staffing")


class StaffingService:
    """Multi-disciplinary staffing conference orchestration service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StaffingRepo(db)
        self.cal_repo = CalendarRepo(db)
        self.perm_service = PermissionService(db)

    async def create_session(
        self,
        session_date: datetime,
        title: str,
        facilitator_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        cadence: str = "WEEKLY",
        status_val: str = "SCHEDULED",
        location: str | None = None,
        minutes: str | None = None,
        attendee_ids: list[uuid.UUID] | None = None,
        case_ids: list[uuid.UUID] | None = None,
        current_user: User | None = None,
    ) -> StaffingSession:
        if current_user:
            has_perm = await self.perm_service.user_has_permission(current_user.id, Permissions.STAFFING_CREATE)
            if not has_perm:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Lacks staffing.create permission.")

        session = await self.repo.create_session(
            session_date=session_date,
            title=title,
            facilitator_id=facilitator_id or (current_user.id if current_user else None),
            team_id=team_id,
            cadence=cadence,
            status=status_val,
            location=location,
            minutes=minutes,
            created_by=current_user.id if current_user else None,
            attendee_ids=attendee_ids,
            case_ids=case_ids,
        )

        # Synchronize with unified calendar representation
        end_at = session_date + timedelta(hours=2)
        await self.cal_repo.create(
            event_type="STAFFING",
            title=f"Staffing: {title}",
            start_at=session_date,
            end_at=end_at,
            location=location,
            source_entity_type="staffing_session",
            source_entity_id=session.id,
            team_id=team_id,
            assigned_user_id=facilitator_id or (current_user.id if current_user else None),
            status=status_val,
            created_by=current_user.id if current_user else None,
        )

        return session

    async def get_session(self, session_id: uuid.UUID, current_user: User | None = None) -> StaffingSessionResponse:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staffing session not found.")

        # Build response
        attendee_resps = [
            StaffingAttendeeResponse(
                id=a.id,
                session_id=a.session_id,
                user_id=a.user_id,
                attendance_status=a.attendance_status,
                notes=a.notes,
                created_at=a.created_at,
                user_name=a.user.full_name if a.user else None,
                user_email=a.user.email if a.user else None,
            )
            for a in session.attendees
        ]

        case_resps = []
        for sc in session.cases:
            # Check case restriction
            if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, sc.case_id):
                continue
            case_resps.append(
                StaffingCaseResponse(
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
            )

        return StaffingSessionResponse(
            id=session.id,
            session_date=session.session_date,
            title=session.title,
            facilitator_id=session.facilitator_id,
            team_id=session.team_id,
            cadence=session.cadence,
            status=session.status,
            location=session.location,
            minutes=session.minutes,
            created_at=session.created_at,
            updated_at=session.updated_at,
            created_by=session.created_by,
            updated_by=session.updated_by,
            facilitator_name=session.facilitator.full_name if session.facilitator else None,
            team_name=session.team.name if session.team else None,
            attendees_count=len(session.attendees),
            cases_count=len(case_resps),
            attendees=attendee_resps,
            cases=case_resps,
        )

    async def list_sessions(
        self,
        status_val: str | None = None,
        team_id: uuid.UUID | None = None,
        facilitator_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
        current_user: User | None = None,
    ) -> tuple[list[StaffingSessionResponse], int]:
        sessions, total = await self.repo.list_sessions(
            status=status_val,
            team_id=team_id,
            facilitator_id=facilitator_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )

        resps = []
        for s in sessions:
            resps.append(
                StaffingSessionResponse(
                    id=s.id,
                    session_date=s.session_date,
                    title=s.title,
                    facilitator_id=s.facilitator_id,
                    team_id=s.team_id,
                    cadence=s.cadence,
                    status=s.status,
                    location=s.location,
                    minutes=s.minutes,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    created_by=s.created_by,
                    updated_by=s.updated_by,
                    facilitator_name=s.facilitator.full_name if s.facilitator else None,
                    team_name=s.team.name if s.team else None,
                    attendees_count=len(s.attendees),
                    cases_count=len(s.cases),
                    attendees=[],
                    cases=[],
                )
            )
        return resps, total

    async def update_session(
        self, session_id: uuid.UUID, update_data: dict[str, Any], current_user: User | None = None
    ) -> StaffingSessionResponse:
        if current_user:
            has_perm = await self.perm_service.user_has_permission(current_user.id, Permissions.STAFFING_UPDATE)
            if not has_perm:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Lacks staffing.update permission.")

        session = await self.repo.update_session(
            session_id=session_id,
            update_data=update_data,
            updated_by=current_user.id if current_user else None,
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staffing session not found.")

        # Update linked calendar event if date or title changed
        cal_evt = await self.cal_repo.get_by_source("staffing_session", session.id)
        if cal_evt:
            cal_updates = {}
            if "title" in update_data:
                cal_updates["title"] = f"Staffing: {session.title}"
            if "session_date" in update_data:
                cal_updates["start_at"] = session.session_date
                cal_updates["end_at"] = session.session_date + timedelta(hours=2)
            if "location" in update_data:
                cal_updates["location"] = session.location
            if "status" in update_data:
                cal_updates["status"] = session.status
            if cal_updates:
                await self.cal_repo.update(cal_evt.id, cal_updates, updated_by=current_user.id if current_user else None)

        return await self.get_session(session.id, current_user)

    async def add_attendee(
        self, session_id: uuid.UUID, user_id: uuid.UUID, status_val: str = "PENDING", notes: str | None = None, current_user: User | None = None
    ) -> StaffingAttendee:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staffing session not found.")
        return await self.repo.add_attendee(session_id, user_id, status=status_val, notes=notes)

    async def add_case(
        self,
        session_id: uuid.UUID,
        case_id: uuid.UUID,
        review_status: str = "PENDING",
        discussion_summary: str | None = None,
        follow_up_required: bool = False,
        follow_up_date: date | None = None,
        assigned_worker_id: uuid.UUID | None = None,
        current_user: User | None = None,
    ) -> StaffingCase:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staffing session not found.")
        if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, case_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Case restriction active.")

        return await self.repo.add_case(
            session_id=session_id,
            case_id=case_id,
            review_status=review_status,
            discussion_summary=discussion_summary,
            follow_up_required=follow_up_required,
            follow_up_date=follow_up_date,
            assigned_worker_id=assigned_worker_id,
        )

    async def update_case_review(
        self, session_id: uuid.UUID, case_id: uuid.UUID, update_data: dict[str, Any], current_user: User | None = None
    ) -> StaffingCase:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staffing session not found.")
        if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, case_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Case restriction active.")

        sc = await self.repo.update_case_review(session_id, case_id, update_data)
        if not sc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case is not attached to this staffing session.")
        return sc

    async def complete_session(
        self, session_id: uuid.UUID, minutes: str | None = None, current_user: User | None = None
    ) -> StaffingSessionResponse:
        """Command endpoint completing a staffing session, finalizing reviews and updating derived last-staffed status."""
        if current_user:
            has_perm = await self.perm_service.user_has_permission(current_user.id, Permissions.STAFFING_COMPLETE)
            if not has_perm:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Lacks staffing.complete permission.")

        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staffing session not found.")

        # Mark all pending cases in this session as reviewed if not explicitly deferred
        for sc in session.cases:
            if sc.review_status == "PENDING":
                sc.review_status = "REVIEWED"

        updates: dict[str, Any] = {"status": "COMPLETED"}
        if minutes is not None:
            updates["minutes"] = minutes

        await self.repo.update_session(session.id, updates, updated_by=current_user.id if current_user else None)

        # Update calendar event status
        cal_evt = await self.cal_repo.get_by_source("staffing_session", session.id)
        if cal_evt:
            await self.cal_repo.update(cal_evt.id, {"status": "COMPLETED"}, updated_by=current_user.id if current_user else None)

        return await self.get_session(session.id, current_user)

    async def get_case_buckets(self, team_id: uuid.UUID | None = None, current_user: User | None = None) -> StaffingCaseBucketsResponse:
        """Retrieve automated server-side case triage buckets."""
        raw_buckets = await self.repo.get_triage_buckets(team_id=team_id)

        # Filter any restricted cases for current user
        filtered_90 = []
        for item in raw_buckets["not_staffed_90_days"]:
            if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, item["case_id"]):
                continue
            filtered_90.append(item)

        filtered_12 = []
        for item in raw_buckets["open_12_months"]:
            if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, item["case_id"]):
                continue
            filtered_12.append(item)

        filtered_risk = []
        for item in raw_buckets["high_risk"]:
            if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, item["case_id"]):
                continue
            filtered_risk.append(item)

        filtered_notes = []
        for item in raw_buckets["missing_recent_note"]:
            if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, item["case_id"]):
                continue
            filtered_notes.append(item)

        return StaffingCaseBucketsResponse(
            not_staffed_90_days=filtered_90,
            open_12_months=filtered_12,
            high_risk=filtered_risk,
            missing_recent_note=filtered_notes,
        )
