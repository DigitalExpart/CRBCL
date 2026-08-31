"""Referral and Intake repository."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.referral import (
    ChildDisposition,
    IntakeDecision,
    Referral,
    ReferralConcern,
    ReferralIncident,
    ReferralLink,
    ReferralPerson,
    ReferralReporter,
    ReferralSequence,
)


class ReferralRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_referral_number(self, target_date: date | None = None) -> str:
        """Concurrency-safe sequence generator for referral numbers (INT-YYYY-NNNNNN)."""
        current_year = (target_date or date.today()).year

        # Query sequence with row lock where possible
        stmt = (
            select(ReferralSequence)
            .where(ReferralSequence.year == current_year)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        seq = result.scalar_one_or_none()

        if not seq:
            seq = ReferralSequence(year=current_year, last_value=1)
            self.db.add(seq)
            await self.db.flush()
            next_val = 1
        else:
            seq.last_value += 1
            next_val = seq.last_value
            await self.db.flush()

        return f"INT-{current_year}-{next_val:06d}"

    async def create(self, referral_data: dict) -> Referral:
        """Create a new referral record."""
        if "referral_number" not in referral_data or not referral_data["referral_number"]:
            rec_date = referral_data.get("received_date") or date.today()
            referral_data["referral_number"] = await self.generate_referral_number(rec_date)

        referral = Referral(**referral_data)
        self.db.add(referral)
        await self.db.flush()
        return referral

    async def get_by_id(self, referral_id: uuid.UUID) -> Referral | None:
        """Retrieve referral by ID with basic relations."""
        stmt = (
            select(Referral)
            .options(
                selectinload(Referral.people).selectinload(ReferralPerson.person),
                selectinload(Referral.reporter),
                selectinload(Referral.incidents),
                selectinload(Referral.concerns),
                selectinload(Referral.dispositions).selectinload(ChildDisposition.person),
                selectinload(Referral.decision),
                selectinload(Referral.outgoing_links).selectinload(ReferralLink.target_referral),
            )
            .where(Referral.id == referral_id, Referral.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, referral_id: uuid.UUID, update_data: dict) -> Referral | None:
        """Update referral metadata (does not change status directly)."""
        referral = await self.get_by_id(referral_id)
        if not referral:
            return None

        for k, v in update_data.items():
            if hasattr(referral, k) and v is not None:
                setattr(referral, k, v)

        referral.version += 1
        referral.updated_at = datetime.now(UTC)
        await self.db.flush()
        return referral

    async def list_referrals(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_worker_id: uuid.UUID | None = None,
        assigned_team_id: uuid.UUID | None = None,
        concern_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Referral], int]:
        """List referrals with multi-criteria filtering and server-side pagination."""
        query = select(Referral).where(Referral.deleted_at.is_(None))

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Referral.referral_number.ilike(search_pattern),
                    Referral.summary.ilike(search_pattern),
                    Referral.community.ilike(search_pattern),
                    Referral.origin_agency.ilike(search_pattern),
                )
            )

        if status:
            query = query.where(Referral.status == status)

        if priority:
            query = query.where(Referral.priority == priority)

        if assigned_worker_id:
            query = query.where(Referral.assigned_worker_id == assigned_worker_id)

        if assigned_team_id:
            query = query.where(Referral.assigned_team_id == assigned_team_id)

        if date_from:
            query = query.where(Referral.received_date >= date_from)

        if date_to:
            query = query.where(Referral.received_date <= date_to)

        if concern_type:
            query = query.join(Referral.concerns).where(ReferralConcern.concern_type == concern_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Fetch page
        offset = (page - 1) * page_size
        query = (
            query.options(
                selectinload(Referral.people),
                selectinload(Referral.concerns),
            )
            .order_by(Referral.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items_result = await self.db.execute(query)
        items = list(items_result.scalars().all())

        return items, total

    async def list_pending_approvals(
        self,
        page: int = 1,
        page_size: int = 20,
        team_id: uuid.UUID | None = None,
    ) -> tuple[list[Referral], int]:
        """Fetch all referrals pending supervisor approval."""
        return await self.list_referrals(
            page=page,
            page_size=page_size,
            status="PENDING_SUPERVISOR",
            assigned_team_id=team_id,
        )

    # ── Person Associations ───────────────────────────────────

    async def add_person(
        self,
        referral_id: uuid.UUID,
        person_id: uuid.UUID,
        role: str,
        relationship_to_child: str | None = None,
        is_primary_caregiver: bool = False,
        is_subject_of_concern: bool = False,
        notes: str | None = None,
    ) -> ReferralPerson:
        """Associate a person to a referral."""
        # Check if already associated
        stmt = select(ReferralPerson).where(
            ReferralPerson.referral_id == referral_id,
            ReferralPerson.person_id == person_id,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.role = role
            existing.relationship_to_child = relationship_to_child
            existing.is_primary_caregiver = is_primary_caregiver
            existing.is_subject_of_concern = is_subject_of_concern
            existing.notes = notes
            await self.db.flush()
            return existing

        rp = ReferralPerson(
            referral_id=referral_id,
            person_id=person_id,
            role=role,
            relationship_to_child=relationship_to_child,
            is_primary_caregiver=is_primary_caregiver,
            is_subject_of_concern=is_subject_of_concern,
            notes=notes,
        )
        self.db.add(rp)
        await self.db.flush()
        return rp

    async def remove_person(self, referral_id: uuid.UUID, person_id: uuid.UUID) -> bool:
        """Remove a person association from a referral."""
        stmt = delete(ReferralPerson).where(
            ReferralPerson.referral_id == referral_id,
            ReferralPerson.person_id == person_id,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    # ── Reporter ──────────────────────────────────────────────

    async def save_reporter(self, referral_id: uuid.UUID, reporter_data: dict) -> ReferralReporter:
        """Save or update confidential reporter details."""
        stmt = select(ReferralReporter).where(ReferralReporter.referral_id == referral_id)
        res = await self.db.execute(stmt)
        reporter = res.scalar_one_or_none()

        if reporter:
            for k, v in reporter_data.items():
                if hasattr(reporter, k):
                    setattr(reporter, k, v)
        else:
            reporter = ReferralReporter(referral_id=referral_id, **reporter_data)
            self.db.add(reporter)

        await self.db.flush()
        return reporter

    # ── Incidents & Concerns ──────────────────────────────────

    async def add_incident(self, referral_id: uuid.UUID, incident_data: dict) -> ReferralIncident:
        incident = ReferralIncident(referral_id=referral_id, **incident_data)
        self.db.add(incident)
        await self.db.flush()
        return incident

    async def add_concern(self, referral_id: uuid.UUID, concern_data: dict) -> ReferralConcern:
        concern = ReferralConcern(referral_id=referral_id, **concern_data)
        self.db.add(concern)
        await self.db.flush()
        return concern

    async def remove_concern(self, referral_id: uuid.UUID, concern_id: uuid.UUID) -> bool:
        stmt = delete(ReferralConcern).where(
            ReferralConcern.referral_id == referral_id,
            ReferralConcern.id == concern_id,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    # ── Dispositions & Decisions ──────────────────────────────

    async def save_child_disposition(
        self,
        referral_id: uuid.UUID,
        person_id: uuid.UUID,
        disposition_data: dict,
        decided_by: uuid.UUID | None = None,
    ) -> ChildDisposition:
        """Save or update a child disposition."""
        stmt = select(ChildDisposition).where(
            ChildDisposition.referral_id == referral_id,
            ChildDisposition.person_id == person_id,
        )
        res = await self.db.execute(stmt)
        disp = res.scalar_one_or_none()

        if disp:
            for k, v in disposition_data.items():
                if hasattr(disp, k):
                    setattr(disp, k, v)
            if decided_by:
                disp.decided_by = decided_by
                disp.decided_at = datetime.now(UTC)
        else:
            disp = ChildDisposition(
                referral_id=referral_id,
                person_id=person_id,
                decided_by=decided_by,
                decided_at=datetime.now(UTC) if decided_by else None,
                **disposition_data,
            )
            self.db.add(disp)

        await self.db.flush()
        return disp

    async def save_decision(
        self,
        referral_id: uuid.UUID,
        overall_recommendation: str,
        rationale: str,
        submitted_by: uuid.UUID | None = None,
    ) -> IntakeDecision:
        """Save or update intake decision recommendation."""
        stmt = select(IntakeDecision).where(IntakeDecision.referral_id == referral_id)
        res = await self.db.execute(stmt)
        decision = res.scalar_one_or_none()

        if decision:
            decision.overall_recommendation = overall_recommendation
            decision.rationale = rationale
            if submitted_by:
                decision.submitted_by = submitted_by
                decision.submitted_at = datetime.now(UTC)
        else:
            decision = IntakeDecision(
                referral_id=referral_id,
                overall_recommendation=overall_recommendation,
                rationale=rationale,
                submitted_by=submitted_by,
                submitted_at=datetime.now(UTC) if submitted_by else None,
            )
            self.db.add(decision)

        await self.db.flush()
        return decision

    # ── Referral Links ────────────────────────────────────────

    async def create_link(
        self,
        source_referral_id: uuid.UUID,
        target_referral_id: uuid.UUID,
        link_type: str,
        reason: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> ReferralLink:
        """Create a relational link between two referrals."""
        if source_referral_id == target_referral_id:
            raise ValueError("Cannot link a referral to itself")

        stmt = select(ReferralLink).where(
            ReferralLink.source_referral_id == source_referral_id,
            ReferralLink.target_referral_id == target_referral_id,
            ReferralLink.link_type == link_type,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        link = ReferralLink(
            source_referral_id=source_referral_id,
            target_referral_id=target_referral_id,
            link_type=link_type,
            reason=reason,
            created_by=created_by,
        )
        self.db.add(link)
        await self.db.flush()
        return link

    async def delete_link(self, link_id: uuid.UUID) -> bool:
        stmt = delete(ReferralLink).where(ReferralLink.id == link_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0
