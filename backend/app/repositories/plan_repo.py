"""Repository for Plans, Versions, Goals, Activities, Signatures."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.plan import (
    Plan,
    PlanActivity,
    PlanAssessment,
    PlanConcern,
    PlanGoal,
    PlanParticipant,
    PlanSequence,
    PlanStrength,
    PlanVersion,
)


class PlanRepository:
    """PostgreSQL data access layer for Plans and sub-resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def next_plan_number(self) -> str:
        """Atomically generate the next sequential Plan number: PLN-YYYYMM-NNNN."""
        now = datetime.now(UTC)
        period = now.strftime("%Y%m")

        stmt = (
            pg_insert(PlanSequence)
            .values(period=period, last_value=1)
            .on_conflict_do_update(
                index_elements=["period"],
                set_={"last_value": PlanSequence.last_value + 1},
            )
            .returning(PlanSequence.last_value)
        )
        result = await self.db.execute(stmt)
        val = result.scalar_one()
        return f"PLN-{period}-{val:04d}"

    async def get_plan_by_id(self, plan_id: uuid.UUID) -> Plan | None:
        """Fetch Plan by ID with all versions and child entities eagerly loaded."""
        stmt = (
            select(Plan)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Plan.case),
                selectinload(Plan.primary_person),
                selectinload(Plan.family),
                selectinload(Plan.creator),
                selectinload(Plan.updater),
                selectinload(Plan.assessments).selectinload(PlanAssessment.assessment),
                selectinload(Plan.versions).selectinload(PlanVersion.participants),
                selectinload(Plan.versions).selectinload(PlanVersion.concerns),
                selectinload(Plan.versions).selectinload(PlanVersion.strengths),
                selectinload(Plan.versions).selectinload(PlanVersion.goals).selectinload(PlanGoal.activities),
                selectinload(Plan.versions).selectinload(PlanVersion.goals).selectinload(PlanGoal.progress_updates),
                selectinload(Plan.versions).selectinload(PlanVersion.signatures),
            )
            .where(Plan.id == plan_id, Plan.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_plans_by_case(self, case_id: uuid.UUID, plan_type: str | None = None) -> list[Plan]:
        """List all non-deleted plans for a case."""
        stmt = (
            select(Plan)
            .options(
                selectinload(Plan.case),
                selectinload(Plan.primary_person),
                selectinload(Plan.family),
                selectinload(Plan.versions).selectinload(PlanVersion.goals).selectinload(PlanGoal.activities),
                selectinload(Plan.versions).selectinload(PlanVersion.signatures),
                selectinload(Plan.assessments),
            )
            .where(Plan.case_id == case_id, Plan.deleted_at.is_(None))
            .order_by(Plan.created_at.desc())
        )
        if plan_type:
            stmt = stmt.where(Plan.plan_type == plan_type)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_plan(
        self,
        *,
        case_id: uuid.UUID,
        primary_person_id: uuid.UUID | None,
        family_id: uuid.UUID | None,
        plan_type: str,
        title: str,
        meeting_date: datetime | None,
        meeting_location: str | None,
        narrative: str | None,
        created_by: uuid.UUID,
        assessment_ids: list[uuid.UUID] | None = None,
        participants: list[dict[str, Any]] | None = None,
        concerns: list[dict[str, Any]] | None = None,
        strengths: list[dict[str, Any]] | None = None,
        goals: list[dict[str, Any]] | None = None,
    ) -> Plan:
        """Create master Plan and initial Version 1 with all child structures."""
        plan_number = await self.next_plan_number()
        plan_id = uuid.uuid4()
        version_id = uuid.uuid4()

        plan = Plan(
            id=plan_id,
            case_id=case_id,
            primary_person_id=primary_person_id,
            family_id=family_id,
            plan_type=plan_type,
            plan_number=plan_number,
            title=title,
            status="DRAFT",
            current_version_id=version_id,
            created_by=created_by,
        )
        self.db.add(plan)

        version = PlanVersion(
            id=version_id,
            plan_id=plan_id,
            version_number=1,
            status="DRAFT",
            meeting_date=meeting_date,
            meeting_location=meeting_location,
            narrative=narrative,
            created_by=created_by,
        )
        self.db.add(version)

        # Participants
        if participants:
            for p in participants:
                part = PlanParticipant(
                    id=uuid.uuid4(),
                    plan_version_id=version_id,
                    participant_type=p.get("participant_type", "WORKER"),
                    user_id=p.get("user_id"),
                    person_id=p.get("person_id"),
                    provider_id=p.get("provider_id"),
                    name=p["name"],
                    relationship=p.get("relationship"),
                    role=p.get("role"),
                    attendance_status=p.get("attendance_status", "ATTENDED"),
                    signature_required=p.get("signature_required", True),
                )
                self.db.add(part)

        # Concerns
        if concerns:
            for idx, c in enumerate(concerns):
                concern = PlanConcern(
                    id=uuid.uuid4(),
                    plan_version_id=version_id,
                    concern_type=c.get("concern_type", "SAFETY_CONCERN"),
                    statement=c["statement"],
                    severity=c.get("severity"),
                    sort_order=c.get("sort_order", idx),
                )
                self.db.add(concern)

        # Strengths
        if strengths:
            for idx, s in enumerate(strengths):
                strength = PlanStrength(
                    id=uuid.uuid4(),
                    plan_version_id=version_id,
                    category=s.get("category"),
                    statement=s["statement"],
                    sort_order=s.get("sort_order", idx),
                )
                self.db.add(strength)

        # Goals & Activities
        if goals:
            for g_idx, g in enumerate(goals):
                goal_id = uuid.uuid4()
                goal = PlanGoal(
                    id=goal_id,
                    plan_version_id=version_id,
                    goal_text=g["goal_text"],
                    category=g.get("category"),
                    target_date=g.get("target_date"),
                    status=g.get("status", "NOT_STARTED"),
                    sort_order=g.get("sort_order", g_idx),
                    created_by=created_by,
                )
                self.db.add(goal)

                for a_idx, a in enumerate(g.get("activities", [])):
                    activity = PlanActivity(
                        id=uuid.uuid4(),
                        goal_id=goal_id,
                        activity_text=a["activity_text"],
                        responsible_type=a.get("responsible_type", "WORKER"),
                        responsible_user_id=a.get("responsible_user_id"),
                        responsible_person_id=a.get("responsible_person_id"),
                        responsible_name=a.get("responsible_name"),
                        due_date=a.get("due_date"),
                        status=a.get("status", "NOT_STARTED"),
                        sort_order=a.get("sort_order", a_idx),
                    )
                    self.db.add(activity)

        # Assessments
        if assessment_ids:
            for asm_id in assessment_ids:
                link = PlanAssessment(
                    id=uuid.uuid4(),
                    plan_id=plan_id,
                    assessment_id=asm_id,
                    relationship_type="INFORMED_BY",
                )
                self.db.add(link)

        await self.db.flush()
        return await self.get_plan_by_id(plan_id)  # type: ignore

    async def get_version_by_id(self, version_id: uuid.UUID) -> PlanVersion | None:
        """Fetch PlanVersion with all child entities eagerly loaded."""
        stmt = (
            select(PlanVersion)
            .options(
                selectinload(PlanVersion.plan).selectinload(Plan.case),
                selectinload(PlanVersion.participants),
                selectinload(PlanVersion.concerns),
                selectinload(PlanVersion.strengths),
                selectinload(PlanVersion.goals).selectinload(PlanGoal.activities),
                selectinload(PlanVersion.goals).selectinload(PlanGoal.progress_updates),
                selectinload(PlanVersion.signatures),
                selectinload(PlanVersion.creator),
                selectinload(PlanVersion.finalizer),
                selectinload(PlanVersion.locker),
            )
            .where(PlanVersion.id == version_id, PlanVersion.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_goal_by_id(self, goal_id: uuid.UUID) -> PlanGoal | None:
        """Fetch goal by ID."""
        stmt = (
            select(PlanGoal)
            .options(
                selectinload(PlanGoal.plan_version).selectinload(PlanVersion.plan),
                selectinload(PlanGoal.activities),
                selectinload(PlanGoal.progress_updates),
            )
            .where(PlanGoal.id == goal_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_activity_by_id(self, activity_id: uuid.UUID) -> PlanActivity | None:
        """Fetch activity by ID."""
        stmt = (
            select(PlanActivity)
            .options(
                selectinload(PlanActivity.goal).selectinload(PlanGoal.plan_version).selectinload(PlanVersion.plan),
            )
            .where(PlanActivity.id == activity_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_goals_by_case(self, case_id: uuid.UUID) -> list[PlanGoal]:
        """Fetch active goals for a case across all active plans."""
        stmt = (
            select(PlanGoal)
            .join(PlanVersion, PlanGoal.plan_version_id == PlanVersion.id)
            .join(Plan, PlanVersion.plan_id == Plan.id)
            .options(
                selectinload(PlanGoal.plan_version).selectinload(PlanVersion.plan),
                selectinload(PlanGoal.activities),
            )
            .where(
                Plan.case_id == case_id,
                Plan.deleted_at.is_(None),
                PlanVersion.deleted_at.is_(None),
                PlanGoal.status.in_(["NOT_STARTED", "IN_PROGRESS", "DEFERRED"]),
            )
            .order_by(PlanGoal.target_date.asc().nulls_last())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
