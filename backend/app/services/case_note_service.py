"""Case note service managing draft/completed/locked lifecycles, addenda, cloning, outbox notifications, and metrics."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.case_note import CaseNote, CaseNoteAddendum, CaseNotePerson
from app.models.user import User
from app.permissions.service import PermissionService
from app.repositories.case_note_repo import CaseNoteRepository
from app.repositories.case_repo import CaseRepository
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class CaseNoteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.note_repo = CaseNoteRepository(db)
        self.case_repo = CaseRepository(db)
        self.perm_service = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def get_note_or_404(self, note_id: uuid.UUID, current_user: User | None = None) -> CaseNote:
        note = await self.note_repo.get_by_id_with_details(note_id)
        if not note or note.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case note not found")

        if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, note.case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

        return note

    async def create_note(
        self,
        case_id: uuid.UUID,
        subject: str,
        content: str,
        note_type: str = "Progress Note",
        duration_minutes: int | None = None,
        contact_type: str | None = None,
        location: str | None = None,
        is_well_child_checkup: bool = False,
        appointment_status: str | None = None,
        next_appointment_at: datetime | None = None,
        goal_id: uuid.UUID | None = None,
        notify_team: bool = False,
        status_val: str = "COMPLETED",
        is_confidential: bool = False,
        people_ids: list[uuid.UUID] | None = None,
        current_user: User | None = None,
    ) -> CaseNote:
        case = await self.case_repo.get(case_id)
        if not case or case.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, case.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Case restriction active.")

        if goal_id:
            from sqlalchemy import select

            from app.models.plan import Plan, PlanGoal, PlanVersion

            goal_stmt = (
                select(PlanGoal)
                .join(PlanVersion, PlanGoal.plan_version_id == PlanVersion.id)
                .join(Plan, PlanVersion.plan_id == Plan.id)
                .where(PlanGoal.id == goal_id, Plan.case_id == case.id, Plan.deleted_at.is_(None))
            )
            goal_res = await self.db.execute(goal_stmt)
            if not goal_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Goal does not belong to this case or does not exist.",
                )

        author_name = (current_user.full_name or current_user.email) if current_user else "Caseworker"

        note = await self.note_repo.create(
            case_id=case.id,
            subject=subject or f"{note_type} - {contact_type or 'Contact'}",
            content=content,
            note_type=note_type,
            duration_minutes=duration_minutes,
            contact_type=contact_type,
            location=location,
            is_well_child_checkup=is_well_child_checkup,
            appointment_status=appointment_status,
            next_appointment_at=next_appointment_at,
            goal_id=goal_id,
            notify_team=notify_team,
            status=status_val,
            is_confidential=is_confidential,
            is_locked=False,
            author_name=author_name,
            created_by=current_user.id if current_user else None,
        )

        # Attach people involved in note
        if people_ids:
            for pid in people_ids:
                self.db.add(CaseNotePerson(case_note_id=note.id, person_id=pid))

        # Sacred Timeline
        await self.timeline.record_event(
            event_type="CASE_NOTE_ADDED",
            title=f"Note: {note.subject}",
            description=f"{note.note_type} recorded by {author_name}.",
            entity_type="case_note",
            entity_id=note.id,
            case_id=case.id,
            created_by=current_user.id if current_user else None,
        )

        # Audit Log
        await self.audit.log_event(
            event_type="CASE_NOTE_CREATED",
            entity_type="case_note",
            entity_id=note.id,
            after_data={
                "case_id": str(case.id),
                "subject": note.subject,
                "note_type": note.note_type,
                "contact_type": note.contact_type,
            },
            user_id=current_user.id if current_user else None,
        )

        # Transactional Outbox Event
        await self.outbox.enqueue(
            event_type="CASE_NOTE_CREATED",
            aggregate_type="case_note",
            aggregate_id=note.id,
            payload={
                "case_id": str(case.id),
                "note_id": str(note.id),
                "subject": note.subject,
                "author": author_name,
                "case_number": case.case_number,
                "notify_team": notify_team,
            },
        )

        # Synchronize follow-up with unified calendar
        if next_appointment_at:
            from app.services.calendar_service import CalendarService

            await CalendarService(self.db).sync_case_note_followup(
                case_note_id=note.id,
                case_id=case.id,
                next_appointment_at=next_appointment_at,
                subject=note.subject,
                current_user=current_user,
            )

        await self.db.commit()
        return await self.get_note_or_404(note.id)

    async def update_note(
        self,
        note_id: uuid.UUID,
        update_data: dict,
        current_user: User,
    ) -> CaseNote:
        """Update case note (strictly rejected if note is LOCKED)."""
        note = await self.get_note_or_404(note_id, current_user)

        # Immutability Check (ADR-011)
        if note.is_locked or note.status == "LOCKED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Case note is legally locked and immutable. Add a supervisor-authorized addendum instead.",
            )

        if update_data.get("goal_id"):
            from sqlalchemy import select

            from app.models.plan import Plan, PlanGoal, PlanVersion

            goal_stmt = (
                select(PlanGoal)
                .join(PlanVersion, PlanGoal.plan_version_id == PlanVersion.id)
                .join(Plan, PlanVersion.plan_id == Plan.id)
                .where(PlanGoal.id == update_data["goal_id"], Plan.case_id == note.case_id, Plan.deleted_at.is_(None))
            )
            goal_res = await self.db.execute(goal_stmt)
            if not goal_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Goal does not belong to this case or does not exist.",
                )

        for key, val in update_data.items():
            if hasattr(note, key) and key not in (
                "id",
                "case_id",
                "created_at",
                "created_by",
                "is_locked",
                "locked_at",
            ):
                setattr(note, key, val)

        note.updated_at = datetime.now(UTC)
        note.updated_by = current_user.id

        await self.audit.log_event(
            event_type="CASE_NOTE_UPDATED",
            entity_type="case_note",
            entity_id=note.id,
            after_data=update_data,
            user_id=current_user.id,
        )

        if "next_appointment_at" in update_data:
            from app.services.calendar_service import CalendarService

            await CalendarService(self.db).sync_case_note_followup(
                case_note_id=note.id,
                case_id=note.case_id,
                next_appointment_at=note.next_appointment_at,
                subject=note.subject,
                current_user=current_user,
            )

        await self.db.commit()
        return await self.get_note_or_404(note.id)

    async def complete_note(
        self,
        note_id: uuid.UUID,
        current_user: User,
    ) -> CaseNote:
        note = await self.get_note_or_404(note_id, current_user)
        if note.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note is already locked.")

        note.status = "COMPLETED"
        note.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_note_or_404(note.id)

    async def lock_note(
        self,
        note_id: uuid.UUID,
        current_user: User,
    ) -> CaseNote:
        """Lock note for legal and evidential immutability."""
        note = await self.get_note_or_404(note_id, current_user)
        if note.is_locked:
            return note

        note.is_locked = True
        note.status = "LOCKED"
        note.locked_at = datetime.now(UTC)
        note.locked_by = current_user.id

        await self.timeline.record_event(
            event_type="CASE_NOTE_LOCKED",
            title=f"Note Locked: {note.subject}",
            description=f"Note legally locked by {current_user.full_name or current_user.email}.",
            entity_type="case_note",
            entity_id=note.id,
            case_id=note.case_id,
            created_by=current_user.id,
        )

        await self.audit.log_event(
            event_type="CASE_NOTE_LOCKED",
            entity_type="case_note",
            entity_id=note.id,
            after_data={"is_locked": True, "locked_at": note.locked_at.isoformat()},
            user_id=current_user.id,
        )

        await self.db.commit()
        return await self.get_note_or_404(note.id)

    async def add_addendum(
        self,
        note_id: uuid.UUID,
        content: str,
        reason: str,
        current_user: User,
    ) -> CaseNoteAddendum:
        """Add an immutable correction or addendum to a case note."""
        note = await self.get_note_or_404(note_id, current_user)

        addendum = CaseNoteAddendum(
            case_note_id=note.id,
            content=content,
            reason=reason,
            created_by=current_user.id,
            created_at=datetime.now(UTC),
        )
        self.db.add(addendum)

        await self.timeline.record_event(
            event_type="CASE_NOTE_CORRECTED",
            title=f"Addendum Appended: {note.subject}",
            description=f"Addendum added by {current_user.full_name or current_user.email}. Reason: {reason}",
            entity_type="case_note",
            entity_id=note.id,
            case_id=note.case_id,
            created_by=current_user.id,
        )

        await self.audit.log_event(
            event_type="CASE_NOTE_ADDENDUM_ADDED",
            entity_type="case_note",
            entity_id=note.id,
            after_data={"reason": reason, "content_length": len(content)},
            user_id=current_user.id,
        )

        await self.db.commit()
        await self.db.refresh(addendum)
        return addendum

    async def clone_note(
        self,
        note_id: uuid.UUID,
        current_user: User,
    ) -> CaseNote:
        """Clone structured metadata (contact type, location, note type) into a fresh DRAFT note."""
        source_note = await self.get_note_or_404(note_id, current_user)

        cloned_note = await self.note_repo.create(
            case_id=source_note.case_id,
            subject=f"Copy of {source_note.subject}",
            content="",
            note_type=source_note.note_type,
            contact_type=source_note.contact_type,
            location=source_note.location,
            duration_minutes=source_note.duration_minutes,
            is_well_child_checkup=source_note.is_well_child_checkup,
            status="DRAFT",
            is_locked=False,
            is_confidential=source_note.is_confidential,
            author_name=current_user.full_name or current_user.email,
            created_by=current_user.id,
        )

        await self.db.commit()
        return await self.get_note_or_404(cloned_note.id)

    async def export_notes_csv(
        self,
        case_id: uuid.UUID,
        current_user: User,
    ) -> str:
        """Export case notes to CSV with access audit logging."""
        case = await self.case_repo.get(case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        notes, _ = await self.note_repo.list_for_case(case.id, limit=500)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Case Number",
                "Subject",
                "Note Type",
                "Contact Type",
                "Location",
                "Duration (mins)",
                "Appointment Status",
                "Author",
                "Created Date",
                "Status",
                "Is Locked",
                "Narrative",
            ]
        )

        for n in notes:
            writer.writerow(
                [
                    case.case_number,
                    n.subject,
                    n.note_type,
                    n.contact_type or "",
                    n.location or "",
                    n.duration_minutes or "",
                    n.appointment_status or "",
                    n.author_name or "",
                    n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else "",
                    n.status,
                    "Yes" if n.is_locked else "No",
                    n.content,
                ]
            )

        await self.audit.log_event(
            event_type="CASE_NOTES_EXPORTED",
            entity_type="case_notes",
            entity_id=case.id,
            after_data={"format": "csv", "count": len(notes)},
            user_id=current_user.id,
        )
        await self.db.commit()

        return output.getvalue()
