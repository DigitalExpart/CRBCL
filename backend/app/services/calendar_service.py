"""Calendar domain service handling personal/team schedule queries, bounded recurrence, case restrictions, and sync."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEvent, CalendarRecurrenceRule
from app.models.case_management import CaseRestriction
from app.models.placement import CourtEvent, VisitationPlan
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.calendar_repo import CalendarRepo
from app.schemas.calendar import CalendarEventResponse, CalendarRecurrenceRuleResponse

logger = logging.getLogger("crbcl.calendar")


class CalendarService:
    """Unified operational calendar service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CalendarRepo(db)
        self.perm_service = PermissionService(db)

    async def create_event(
        self,
        event_type: str,
        title: str,
        start_at: datetime,
        end_at: datetime,
        all_day: bool = False,
        timezone: str = "America/Regina",
        location: str | None = None,
        description: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
        person_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        assigned_user_id: uuid.UUID | None = None,
        status_val: str = "SCHEDULED",
        recurrence_data: dict[str, Any] | None = None,
        current_user: User | None = None,
    ) -> CalendarEvent:
        if end_at < start_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event end time must be greater than or equal to start time.",
            )

        if case_id and current_user:
            if await self.perm_service.is_user_restricted_from_case(current_user.id, case_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Case restriction active.",
                )

        event = await self.repo.create(
            event_type=event_type,
            title=title,
            start_at=start_at,
            end_at=end_at,
            all_day=all_day,
            timezone=timezone,
            location=location,
            description=description,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            case_id=case_id,
            person_id=person_id,
            team_id=team_id,
            assigned_user_id=assigned_user_id or (current_user.id if current_user else None),
            status=status_val,
            created_by=current_user.id if current_user else None,
            recurrence_data=recurrence_data,
        )
        return event

    async def get_my_schedule(
        self,
        current_user: User,
        start_at: datetime,
        end_at: datetime,
        event_types: list[str] | None = None,
    ) -> list[CalendarEventResponse]:
        """Fetch current user's authorized calendar schedule with case-restriction privacy masking."""
        raw_events = await self.repo.query_schedule(
            start_at=start_at,
            end_at=end_at,
            user_id=current_user.id,
            event_types=event_types,
        )

        results = []
        for evt in raw_events:
            results.append(await self._format_and_sanitize_event(evt, current_user))

        return results

    async def get_team_schedule(
        self,
        current_user: User,
        start_at: datetime,
        end_at: datetime,
        team_id: uuid.UUID | None = None,
        worker_ids: list[uuid.UUID] | None = None,
        event_types: list[str] | None = None,
    ) -> list[CalendarEventResponse]:
        """Fetch supervisor/director team schedule with case-restriction privacy masking."""
        has_team_perm = await self.perm_service.user_has_permission(current_user.id, Permissions.CALENDAR_READ_TEAM)
        if not has_team_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Lacks calendar.read_team permission to view team schedule.",
            )

        raw_events = await self.repo.query_schedule(
            start_at=start_at,
            end_at=end_at,
            team_id=team_id,
            worker_ids=worker_ids,
            event_types=event_types,
        )

        results = []
        for evt in raw_events:
            results.append(await self._format_and_sanitize_event(evt, current_user))

        return results

    async def _format_and_sanitize_event(self, evt: CalendarEvent, viewing_user: User) -> CalendarEventResponse:
        """Sanitize event payload if viewing user has an active case restriction on linked case."""
        is_restricted = False
        if evt.case_id:
            is_restricted = await self.perm_service.is_user_restricted_from_case(viewing_user.id, evt.case_id)

        if is_restricted:
            return CalendarEventResponse(
                id=evt.id,
                event_type=evt.event_type,
                title="Unavailable / Busy",
                start_at=evt.start_at,
                end_at=evt.end_at,
                all_day=evt.all_day,
                timezone=evt.timezone,
                location=None,
                description=None,
                source_entity_type=None,
                source_entity_id=None,
                case_id=None,
                person_id=None,
                team_id=evt.team_id,
                assigned_user_id=evt.assigned_user_id,
                status=evt.status,
                created_at=evt.created_at,
                updated_at=evt.updated_at,
                created_by=None,
                updated_by=None,
                is_redacted=True,
                assigned_user_name=evt.assigned_user.full_name if evt.assigned_user else None,
                case_number=None,
                person_name=None,
                recurrence_rule=None,
            )

        recurrence_resp = None
        if evt.recurrence_rule:
            recurrence_resp = CalendarRecurrenceRuleResponse.model_validate(evt.recurrence_rule)

        return CalendarEventResponse(
            id=evt.id,
            event_type=evt.event_type,
            title=evt.title,
            start_at=evt.start_at,
            end_at=evt.end_at,
            all_day=evt.all_day,
            timezone=evt.timezone,
            location=evt.location,
            description=evt.description,
            source_entity_type=evt.source_entity_type,
            source_entity_id=evt.source_entity_id,
            case_id=evt.case_id,
            person_id=evt.person_id,
            team_id=evt.team_id,
            assigned_user_id=evt.assigned_user_id,
            status=evt.status,
            created_at=evt.created_at,
            updated_at=evt.updated_at,
            created_by=evt.created_by,
            updated_by=evt.updated_by,
            is_redacted=False,
            assigned_user_name=evt.assigned_user.full_name if evt.assigned_user else None,
            case_number=evt.case.case_number if evt.case else None,
            person_name=f"{evt.person.first_name} {evt.person.last_name}" if evt.person else None,
            recurrence_rule=recurrence_resp,
        )

    # ── Source Synchronization Hooks ───────────────────────────

    async def sync_court_event(self, court_event: CourtEvent, current_user: User | None = None) -> CalendarEvent | None:
        """Keep calendar representation synchronized when a CourtEvent is scheduled or modified."""
        existing = await self.repo.get_by_source("court_event", court_event.id)

        # Build start_at from hearing_date and optional hearing_time
        h_time = court_event.hearing_time or time(9, 0)
        start_dt = datetime.combine(court_event.hearing_date, h_time).replace(tzinfo=UTC)
        end_dt = start_dt + timedelta(hours=2)

        title = f"Court Hearing: {court_event.hearing_type.replace('_', ' ').title()}"

        if existing:
            await self.repo.update(
                existing.id,
                {
                    "title": title,
                    "start_at": start_dt,
                    "end_at": end_dt,
                    "location": court_event.court_location,
                    "status": "COMPLETED" if court_event.status == "COMPLETED" else "SCHEDULED",
                },
                updated_by=current_user.id if current_user else None,
            )
            return existing

        return await self.repo.create(
            event_type="COURT",
            title=title,
            start_at=start_dt,
            end_at=end_dt,
            location=court_event.court_location,
            source_entity_type="court_event",
            source_entity_id=court_event.id,
            case_id=court_event.case_id,
            person_id=court_event.child_id,
            status=court_event.status,
            created_by=current_user.id if current_user else None,
        )

    async def sync_case_note_followup(
        self,
        case_note_id: uuid.UUID,
        case_id: uuid.UUID,
        next_appointment_at: datetime | None,
        subject: str,
        current_user: User | None = None,
    ) -> CalendarEvent | None:
        """Create or update follow-up calendar event when CaseNote has next_appointment_at."""
        existing = await self.repo.get_by_source("case_note", case_note_id)

        if not next_appointment_at:
            if existing:
                await self.repo.delete(existing.id, deleted_by=current_user.id if current_user else None)
            return None

        end_dt = next_appointment_at + timedelta(hours=1)
        title = f"Follow-up: {subject or 'Case Note Follow-up'}"

        if existing:
            await self.repo.update(
                existing.id,
                {
                    "title": title,
                    "start_at": next_appointment_at,
                    "end_at": end_dt,
                },
                updated_by=current_user.id if current_user else None,
            )
            return existing

        return await self.repo.create(
            event_type="CASE_NOTE_FOLLOWUP",
            title=title,
            start_at=next_appointment_at,
            end_at=end_dt,
            source_entity_type="case_note",
            source_entity_id=case_note_id,
            case_id=case_id,
            assigned_user_id=current_user.id if current_user else None,
            created_by=current_user.id if current_user else None,
        )
