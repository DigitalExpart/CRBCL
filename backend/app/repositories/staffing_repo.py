"""Staffing repository for sessions, attendees, case reviews, triage buckets, and last-staffed calculation."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.staffing import StaffingAttendee, StaffingCase, StaffingSession


class StaffingRepo:
    """Data access layer for staffing sessions, reviews, and automated case triage buckets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        session_date: datetime,
        title: str,
        facilitator_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        cadence: str = "WEEKLY",
        status: str = "SCHEDULED",
        location: str | None = None,
        minutes: str | None = None,
        created_by: uuid.UUID | None = None,
        attendee_ids: list[uuid.UUID] | None = None,
        case_ids: list[uuid.UUID] | None = None,
    ) -> StaffingSession:
        session = StaffingSession(
            session_date=session_date,
            title=title,
            facilitator_id=facilitator_id,
            team_id=team_id,
            cadence=cadence,
            status=status,
            location=location,
            minutes=minutes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(session)
        await self.db.flush()

        if attendee_ids:
            for uid in attendee_ids:
                attendee = StaffingAttendee(
                    session_id=session.id,
                    user_id=uid,
                    attendance_status="PENDING",
                )
                self.db.add(attendee)

        if case_ids:
            for cid in case_ids:
                sc = StaffingCase(
                    session_id=session.id,
                    case_id=cid,
                    review_status="PENDING",
                )
                self.db.add(sc)

        await self.db.flush()
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> StaffingSession | None:
        stmt = (
            select(StaffingSession)
            .options(
                selectinload(StaffingSession.facilitator),
                selectinload(StaffingSession.team),
                selectinload(StaffingSession.attendees).selectinload(StaffingAttendee.user),
                selectinload(StaffingSession.cases).selectinload(StaffingCase.case),
                selectinload(StaffingSession.cases).selectinload(StaffingCase.assigned_worker),
            )
            .where(StaffingSession.id == session_id, StaffingSession.deleted_at.is_(None))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_sessions(
        self,
        status: str | None = None,
        team_id: uuid.UUID | None = None,
        facilitator_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[StaffingSession], int]:
        conditions = [StaffingSession.deleted_at.is_(None)]

        if status:
            conditions.append(StaffingSession.status == status)
        if team_id:
            conditions.append(StaffingSession.team_id == team_id)
        if facilitator_id:
            conditions.append(StaffingSession.facilitator_id == facilitator_id)
        if from_date:
            conditions.append(StaffingSession.session_date >= from_date)
        if to_date:
            conditions.append(StaffingSession.session_date <= to_date)

        count_stmt = select(func.count(StaffingSession.id)).where(and_(*conditions))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(StaffingSession)
            .options(
                selectinload(StaffingSession.facilitator),
                selectinload(StaffingSession.team),
                selectinload(StaffingSession.attendees).selectinload(StaffingAttendee.user),
                selectinload(StaffingSession.cases).selectinload(StaffingCase.case),
            )
            .where(and_(*conditions))
            .order_by(StaffingSession.session_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def update_session(
        self, session_id: uuid.UUID, update_data: dict[str, Any], updated_by: uuid.UUID | None = None
    ) -> StaffingSession | None:
        session = await self.get_by_id(session_id)
        if not session:
            return None

        for key, val in update_data.items():
            if hasattr(session, key) and val is not None and key not in ("id", "created_at", "created_by"):
                setattr(session, key, val)

        session.updated_at = datetime.now(UTC)
        if updated_by:
            session.updated_by = updated_by

        await self.db.flush()
        return session

    async def add_attendee(
        self, session_id: uuid.UUID, user_id: uuid.UUID, status: str = "PENDING", notes: str | None = None
    ) -> StaffingAttendee:
        # Check if already added
        stmt = select(StaffingAttendee).where(
            StaffingAttendee.session_id == session_id,
            StaffingAttendee.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.attendance_status = status
            if notes is not None:
                existing.notes = notes
            await self.db.flush()
            return existing

        attendee = StaffingAttendee(
            session_id=session_id,
            user_id=user_id,
            attendance_status=status,
            notes=notes,
        )
        self.db.add(attendee)
        await self.db.flush()
        return attendee

    async def add_case(
        self,
        session_id: uuid.UUID,
        case_id: uuid.UUID,
        review_status: str = "PENDING",
        discussion_summary: str | None = None,
        follow_up_required: bool = False,
        follow_up_date: date | None = None,
        assigned_worker_id: uuid.UUID | None = None,
    ) -> StaffingCase:
        stmt = select(StaffingCase).where(
            StaffingCase.session_id == session_id,
            StaffingCase.case_id == case_id,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.review_status = review_status
            if discussion_summary is not None:
                existing.discussion_summary = discussion_summary
            existing.follow_up_required = follow_up_required
            existing.follow_up_date = follow_up_date
            existing.assigned_worker_id = assigned_worker_id
            await self.db.flush()
            return existing

        sc = StaffingCase(
            session_id=session_id,
            case_id=case_id,
            review_status=review_status,
            discussion_summary=discussion_summary,
            follow_up_required=follow_up_required,
            follow_up_date=follow_up_date,
            assigned_worker_id=assigned_worker_id,
        )
        self.db.add(sc)
        await self.db.flush()
        return sc

    async def update_case_review(
        self, session_id: uuid.UUID, case_id: uuid.UUID, update_data: dict[str, Any]
    ) -> StaffingCase | None:
        stmt = select(StaffingCase).where(
            StaffingCase.session_id == session_id,
            StaffingCase.case_id == case_id,
        )
        res = await self.db.execute(stmt)
        sc = res.scalar_one_or_none()
        if not sc:
            return None

        for key, val in update_data.items():
            if hasattr(sc, key) and val is not None:
                setattr(sc, key, val)

        await self.db.flush()
        return sc

    async def get_last_staffed_date(self, case_id: uuid.UUID) -> datetime | None:
        """Derive canonical last staffed date from completed staffing session reviews."""
        stmt = (
            select(func.max(StaffingSession.session_date))
            .join(StaffingCase, StaffingCase.session_id == StaffingSession.id)
            .where(
                StaffingCase.case_id == case_id,
                StaffingCase.review_status == "REVIEWED",
                StaffingSession.status == "COMPLETED",
                StaffingSession.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_triage_buckets(self, team_id: uuid.UUID | None = None) -> dict[str, list[dict[str, Any]]]:
        """Compute server-side triage buckets for active cases."""
        now = datetime.now(UTC)
        threshold_90_days = now - timedelta(days=90)
        threshold_12_months = (now - timedelta(days=365)).date()

        # Query all active non-deleted cases
        case_conditions = [
            Case.status != "Closed",
            Case.deleted_at.is_(None),
        ]
        if team_id:
            case_conditions.append(Case.assigned_team_id == team_id)

        stmt = select(Case).where(and_(*case_conditions)).order_by(Case.created_at.desc())
        res = await self.db.execute(stmt)
        active_cases = list(res.scalars().all())

        not_staffed_90 = []
        open_12_mos = []
        high_risk = []
        missing_notes = []

        for c in active_cases:
            last_staffed = await self.get_last_staffed_date(c.id)
            days_since = (now - last_staffed).days if last_staffed else None

            # Check case notes
            note_stmt = select(func.max(CaseNote.created_at)).where(
                CaseNote.case_id == c.id, CaseNote.deleted_at.is_(None)
            )
            note_res = await self.db.execute(note_stmt)
            last_note = note_res.scalar_one_or_none()

            opened_dt = c.intake_date or (c.created_at.date() if c.created_at else None)
            months_open = None
            if opened_dt:
                months_open = int((now.date() - opened_dt).days / 30.4)

            worker_name = c.assigned_worker_name

            item = {
                "case_id": c.id,
                "case_number": c.case_number,
                "case_title": c.title,
                "stage": c.stage,
                "status": c.status,
                "assigned_worker_name": worker_name,
                "last_staffed_date": last_staffed,
                "days_since_last_staffed": days_since,
                "opened_date": opened_dt,
                "months_open": months_open,
                "risk_level": c.risk_level,
                "last_case_note_date": last_note,
            }

            # Bucket 1: Not Staffed in 90+ days (or never staffed and open > 90 days)
            if last_staffed is None:
                if opened_dt and opened_dt <= (now.date() - timedelta(days=90)):
                    not_staffed_90.append(item)
            elif last_staffed <= threshold_90_days:
                not_staffed_90.append(item)

            # Bucket 2: Open 12+ months
            if opened_dt and opened_dt <= threshold_12_months:
                open_12_mos.append(item)

            # Bucket 3: High Risk
            if getattr(c, "risk_level", None) in ("High", "Critical", "HIGH", "CRITICAL") or getattr(
                c, "is_high_risk", False
            ):
                high_risk.append(item)

            # Bucket 4: Missing Recent Note (no note in 30 days)
            if last_note is None or last_note < (now - timedelta(days=30)):
                missing_notes.append(item)

        return {
            "not_staffed_90_days": not_staffed_90,
            "open_12_months": open_12_mos,
            "high_risk": high_risk,
            "missing_recent_note": missing_notes,
        }
