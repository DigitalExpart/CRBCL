"""Domain Service for Safety Plans, Case Plans, Goals, Activities, Signatures."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.plan import (
    GoalProgressUpdate,
    Plan,
    PlanActivity,
    PlanConcern,
    PlanGoal,
    PlanParticipant,
    PlanSignature,
    PlanStrength,
    PlanVersion,
)
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.plan_repo import PlanRepository
from app.schemas.plan import (
    GoalMetricsResponse,
    PhysicalSignatureUploadRequest,
    PlanActivityCompleteRequest,
    PlanActivityCreate,
    PlanApproveRequest,
    PlanCloneRequest,
    PlanCreate,
    PlanFinalizeRequest,
    PlanGoalCompleteRequest,
    PlanGoalCreate,
    PlanGoalUpdate,
    PlanLockRequest,
    PlanPrintResponse,
    PlanReturnRequest,
    PlanSignatureCreate,
    PlanSubmitRequest,
    PlanSummaryResponse,
    PlanUnlockRequest,
    PlanUpdate,
    PlanVersionCreate,
)
from app.services.signature_service import SignatureService
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class PlanService:
    """Business logic for Family Wellness Plans, Versioning, and Governance."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlanRepository(db)
        self.perm = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def _require_case_access(self, user_id: uuid.UUID, case_id: uuid.UUID) -> None:
        """Check if user has access to case without active restriction."""
        if await self.perm.is_user_restricted_from_case(user_id, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

    async def _require_perm(self, user_id: uuid.UUID, permission_key: str) -> None:
        """Check if user has required permission."""
        if not await self.perm.user_has_permission(user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permission: {permission_key}",
            )

    def _compute_metrics(self, goals: list[PlanGoal]) -> GoalMetricsResponse:
        """Calculate deterministic metrics across goals and activities."""
        today = date.today()
        total_goals = len(goals)
        not_started = sum(1 for g in goals if g.status == "NOT_STARTED")
        in_progress = sum(1 for g in goals if g.status == "IN_PROGRESS")
        completed = sum(1 for g in goals if g.status == "COMPLETED")
        overdue_goals = sum(
            1 for g in goals if g.target_date and g.target_date < today and g.status not in ("COMPLETED", "CANCELLED")
        )

        all_activities: list[PlanActivity] = []
        for g in goals:
            all_activities.extend(g.activities)

        total_activities = len(all_activities)
        completed_activities = sum(1 for a in all_activities if a.status == "COMPLETED")
        overdue_activities = sum(
            1
            for a in all_activities
            if a.due_date and a.due_date < today and a.status not in ("COMPLETED", "CANCELLED")
        )

        pct = (completed / total_goals * 100.0) if total_goals > 0 else 0.0

        return GoalMetricsResponse(
            total_goals=total_goals,
            not_started_goals=not_started,
            in_progress_goals=in_progress,
            completed_goals=completed,
            overdue_goals=overdue_goals,
            total_activities=total_activities,
            completed_activities=completed_activities,
            overdue_activities=overdue_activities,
            completion_percentage=round(pct, 1),
        )

    def _get_current_version(self, plan: Plan) -> PlanVersion:
        """Retrieve current active version or raise 404."""
        if not plan.versions:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan has no versions.")
        if plan.current_version_id:
            for v in plan.versions:
                if v.id == plan.current_version_id:
                    return v
        return plan.versions[0]

    async def create_plan(self, user: User, payload: PlanCreate) -> Plan:
        """Create a new Master Plan and initial Version 1."""
        user_id = user.id
        user_name = user.full_name or user.email

        # 1. Enforce Case Access Restrictions (ADR-010)
        await self._require_case_access(user_id, payload.case_id)

        # 2. Enforce Plan Type Permissions
        await self._require_perm(user_id, Permissions.PLAN_CREATE)
        if payload.plan_type == "SAFETY_PLAN":
            await self._require_perm(user_id, Permissions.PLAN_SAFETY_WRITE)
        elif payload.plan_type == "CASE_PLAN":
            await self._require_perm(user_id, Permissions.PLAN_CASE_WRITE)

        # 3. Create Plan in DB
        plan = await self.repo.create_plan(
            case_id=payload.case_id,
            primary_person_id=payload.primary_person_id,
            family_id=payload.family_id,
            plan_type=payload.plan_type,
            title=payload.title,
            meeting_date=payload.meeting_date,
            meeting_location=payload.meeting_location,
            narrative=payload.narrative,
            created_by=user_id,
            assessment_ids=payload.assessment_ids,
            participants=[p.model_dump() for p in payload.participants],
            concerns=[c.model_dump() for c in payload.concerns],
            strengths=[s.model_dump() for s in payload.strengths],
            goals=[g.model_dump() for g in payload.goals],
        )

        # 4. Sacred Timeline & Audit
        event_type = "SAFETY_PLAN_CREATED" if payload.plan_type == "SAFETY_PLAN" else "CASE_PLAN_CREATED"
        await self.timeline.record_event(
            event_type=event_type,
            title=f"Created {payload.plan_type.replace('_', ' ').title()}: {plan.plan_number}",
            description=f"{payload.title} created by {user_name}.",
            case_id=payload.case_id,
            entity_type="plan",
            entity_id=plan.id,
            created_by=user_id,
        )

        await self.audit.log_event(
            event_type="PLAN_CREATED",
            user_id=user_id,
            entity_type="plan",
            entity_id=plan.id,
            after_data={"plan_number": plan.plan_number, "plan_type": plan.plan_type, "case_id": str(payload.case_id)},
        )

        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    async def get_plan(self, user: User, plan_id: uuid.UUID) -> Plan:
        """Fetch Plan by ID with case restrictions and read permission check."""
        user_id = user.id
        plan = await self.repo.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

        await self._require_case_access(user_id, plan.case_id)
        await self._require_perm(user_id, Permissions.PLAN_READ)

        if plan.plan_type == "SAFETY_PLAN":
            await self._require_perm(user_id, Permissions.PLAN_SAFETY_READ)
        elif plan.plan_type == "CASE_PLAN":
            await self._require_perm(user_id, Permissions.PLAN_CASE_READ)

        return plan

    async def list_case_plans(
        self, user: User, case_id: uuid.UUID, plan_type: str | None = None
    ) -> list[PlanSummaryResponse]:
        """List all plans for a case with computed summary metrics."""
        user_id = user.id
        await self._require_case_access(user_id, case_id)
        await self._require_perm(user_id, Permissions.PLAN_READ)

        plans = await self.repo.list_plans_by_case(case_id, plan_type)
        summaries: list[PlanSummaryResponse] = []

        for p in plans:
            curr_v = self._get_current_version(p)
            metrics = self._compute_metrics(curr_v.goals)
            signatures_count = len(curr_v.signatures)
            signatures_req = sum(1 for part in curr_v.participants if part.signature_required)

            summaries.append(
                PlanSummaryResponse(
                    id=p.id,
                    case_id=p.case_id,
                    plan_type=p.plan_type,
                    plan_number=p.plan_number,
                    title=p.title,
                    status=p.status,
                    current_version_number=curr_v.version_number,
                    meeting_date=curr_v.meeting_date,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    metrics=metrics,
                    signatures_count=signatures_count,
                    signatures_required=signatures_req,
                )
            )

        return summaries

    async def update_plan(self, user: User, plan_id: uuid.UUID, payload: PlanUpdate) -> Plan:
        """Update master plan title and current version metadata."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_UPDATE)

        curr_v = self._get_current_version(plan)
        if curr_v.status in ("FINALIZED", "LOCKED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit plan in {curr_v.status} state. Create a new version or clone.",
            )

        if payload.title is not None:
            plan.title = payload.title
        if payload.primary_person_id is not None:
            plan.primary_person_id = payload.primary_person_id
        if payload.family_id is not None:
            plan.family_id = payload.family_id

        if payload.meeting_date is not None:
            curr_v.meeting_date = payload.meeting_date
        if payload.meeting_location is not None:
            curr_v.meeting_location = payload.meeting_location
        if payload.narrative is not None:
            curr_v.narrative = payload.narrative

        plan.updated_by = user_id
        curr_v.updated_by = user_id
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan_id)  # type: ignore

    # ── Lifecycle Transitions ─────────────────────────────────────────

    async def submit_plan(self, user: User, plan_id: uuid.UUID, payload: PlanSubmitRequest) -> Plan:
        """Submit draft plan for supervisor clinical review."""
        user_id = user.id
        user_name = user.full_name or user.email
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_SUBMIT)

        curr_v = self._get_current_version(plan)
        if curr_v.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan is not in DRAFT state (currently {curr_v.status}).",
            )

        curr_v.status = "IN_REVIEW"
        plan.status = "IN_REVIEW"
        curr_v.updated_by = user_id

        await self.timeline.record_event(
            event_type="PLAN_SUBMITTED",
            title=f"Plan Submitted: {plan.plan_number} v{curr_v.version_number}",
            description=f"Submitted for review by {user_name}. Notes: {payload.comments or 'None'}",
            case_id=plan.case_id,
            entity_type="plan",
            entity_id=plan.id,
            created_by=user_id,
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    async def approve_plan(self, user: User, plan_id: uuid.UUID, payload: PlanApproveRequest) -> Plan:
        """Supervisor approves plan and seals it into FINALIZED state with cryptographic hash."""
        user_id = user.id
        user_name = user.full_name or user.email
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_APPROVE)

        curr_v = self._get_current_version(plan)
        if curr_v.status != "IN_REVIEW":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Plan is not IN_REVIEW (currently {curr_v.status})."
            )

        # Generate canonical document hash
        doc_hash = SignatureService.compute_document_hash(curr_v)
        curr_v.document_hash = doc_hash
        curr_v.status = "FINALIZED"
        curr_v.finalized_at = datetime.now(UTC)
        curr_v.finalized_by = user_id
        plan.status = "FINALIZED"

        await self.timeline.record_event(
            event_type="PLAN_APPROVED",
            title=f"Plan Approved: {plan.plan_number} v{curr_v.version_number}",
            description=f"Approved by {user_name}. SHA-256: {doc_hash[:12]}...",
            case_id=plan.case_id,
            entity_type="plan",
            entity_id=plan.id,
            created_by=user_id,
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    async def return_plan(self, user: User, plan_id: uuid.UUID, payload: PlanReturnRequest) -> Plan:
        """Supervisor returns plan to worker with actionable revisions."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_RETURN)

        curr_v = self._get_current_version(plan)
        if curr_v.status != "IN_REVIEW":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Plan is not IN_REVIEW (currently {curr_v.status})."
            )

        curr_v.status = "DRAFT"
        plan.status = "DRAFT"
        curr_v.updated_by = user_id

        await self.timeline.record_event(
            event_type="PLAN_RETURNED",
            title=f"Plan Returned: {plan.plan_number} v{curr_v.version_number}",
            description=f"Returned for changes: {payload.reasons}",
            case_id=plan.case_id,
            entity_type="plan",
            entity_id=plan.id,
            created_by=user_id,
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    async def finalize_plan(self, user: User, plan_id: uuid.UUID, payload: PlanFinalizeRequest) -> Plan:
        """Directly finalize plan and compute canonical SHA-256 document hash."""
        user_id = user.id
        user_name = user.full_name or user.email
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_FINALIZE)

        curr_v = self._get_current_version(plan)
        if curr_v.status in ("FINALIZED", "LOCKED"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Plan is already {curr_v.status}.")

        doc_hash = SignatureService.compute_document_hash(curr_v)
        curr_v.document_hash = doc_hash
        curr_v.status = "FINALIZED"
        curr_v.finalized_at = datetime.now(UTC)
        curr_v.finalized_by = user_id
        plan.status = "FINALIZED"

        await self.timeline.record_event(
            event_type="PLAN_FINALIZED",
            title=f"Plan Finalized: {plan.plan_number} v{curr_v.version_number}",
            description=f"Finalized by {user_name}. SHA-256: {doc_hash[:12]}...",
            case_id=plan.case_id,
            entity_type="plan",
            entity_id=plan.id,
            created_by=user_id,
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    async def lock_plan(self, user: User, plan_id: uuid.UUID, payload: PlanLockRequest) -> Plan:
        """Lock finalized plan to enforce complete immutability."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_LOCK)

        curr_v = self._get_current_version(plan)
        if curr_v.status != "FINALIZED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only FINALIZED plans can be locked.")

        curr_v.status = "LOCKED"
        curr_v.locked_at = datetime.now(UTC)
        curr_v.locked_by = user_id
        plan.status = "LOCKED"

        await self.audit.log_event(
            event_type="PLAN_LOCKED",
            user_id=user_id,
            entity_type="plan",
            entity_id=plan.id,
            after_data={"reason": payload.reason, "version": curr_v.version_number},
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    async def unlock_plan(self, user: User, plan_id: uuid.UUID, payload: PlanUnlockRequest) -> Plan:
        """Director unlock with mandatory justification."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_UNLOCK)

        curr_v = self._get_current_version(plan)
        if curr_v.status != "LOCKED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan is not LOCKED.")

        curr_v.status = "FINALIZED"
        curr_v.locked_at = None
        curr_v.locked_by = None
        plan.status = "FINALIZED"

        await self.audit.log_event(
            event_type="PLAN_UNLOCKED",
            user_id=user_id,
            entity_type="plan",
            entity_id=plan.id,
            after_data={"justification": payload.justification, "version": curr_v.version_number},
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(plan.id)  # type: ignore

    # ── Versioning & Cloning ──────────────────────────────────────────

    async def create_new_version(self, user: User, plan_id: uuid.UUID, payload: PlanVersionCreate) -> PlanVersion:
        """Create next version on an existing running plan."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_CREATE)

        curr_v = self._get_current_version(plan)
        next_ver_num = curr_v.version_number + 1
        new_v_id = uuid.uuid4()

        new_version = PlanVersion(
            id=new_v_id,
            plan_id=plan.id,
            version_number=next_ver_num,
            status="DRAFT",
            meeting_date=payload.meeting_date or curr_v.meeting_date,
            meeting_location=payload.meeting_location or curr_v.meeting_location,
            narrative=payload.narrative or curr_v.narrative,
            source_version_id=curr_v.id,
            created_by=user_id,
        )
        self.db.add(new_version)

        # Copy participants
        for p in curr_v.participants:
            new_p = PlanParticipant(
                id=uuid.uuid4(),
                plan_version_id=new_v_id,
                participant_type=p.participant_type,
                user_id=p.user_id,
                person_id=p.person_id,
                provider_id=p.provider_id,
                name=p.name,
                relationship=p.relationship,
                role=p.role,
                attendance_status="ATTENDED",
                signature_required=p.signature_required,
            )
            self.db.add(new_p)

        # Copy concerns
        for c in curr_v.concerns:
            new_c = PlanConcern(
                id=uuid.uuid4(),
                plan_version_id=new_v_id,
                concern_type=c.concern_type,
                statement=c.statement,
                severity=c.severity,
                sort_order=c.sort_order,
            )
            self.db.add(new_c)

        # Copy strengths
        for s in curr_v.strengths:
            new_s = PlanStrength(
                id=uuid.uuid4(),
                plan_version_id=new_v_id,
                category=s.category,
                statement=s.statement,
                sort_order=s.sort_order,
            )
            self.db.add(new_s)

        # Copy open/active goals & activities
        for g in curr_v.goals:
            new_g_id = uuid.uuid4()
            new_g = PlanGoal(
                id=new_g_id,
                plan_version_id=new_v_id,
                goal_text=g.goal_text,
                category=g.category,
                target_date=g.target_date,
                status=g.status if g.status != "COMPLETED" else "COMPLETED",
                sort_order=g.sort_order,
                created_by=user_id,
            )
            self.db.add(new_g)

            for a in g.activities:
                new_a = PlanActivity(
                    id=uuid.uuid4(),
                    goal_id=new_g_id,
                    activity_text=a.activity_text,
                    responsible_type=a.responsible_type,
                    responsible_user_id=a.responsible_user_id,
                    responsible_person_id=a.responsible_person_id,
                    responsible_name=a.responsible_name,
                    due_date=a.due_date,
                    status=a.status if a.status != "COMPLETED" else "COMPLETED",
                    sort_order=a.sort_order,
                )
                self.db.add(new_a)

        plan.current_version_id = new_v_id
        plan.status = "DRAFT"
        plan.updated_by = user_id
        await self.db.commit()

        return await self.repo.get_version_by_id(new_v_id)  # type: ignore

    async def clone_plan(self, user: User, plan_id: uuid.UUID, payload: PlanCloneRequest) -> Plan:
        """Clone an existing plan into a brand new Plan entity (new plan number, reset locks/signatures)."""
        user_id = user.id
        user_name = user.full_name or user.email
        source_plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_CLONE)

        source_v = self._get_current_version(source_plan)
        source_case_id = source_plan.case_id
        source_plan_num = source_plan.plan_number
        source_person_id = source_plan.primary_person_id
        source_family_id = source_plan.family_id
        source_type = source_plan.plan_type
        title = payload.new_title or f"Copy of {source_plan.title}"

        # Prepare participants, concerns, strengths, goals
        participants_data = [
            {
                "participant_type": p.participant_type,
                "user_id": p.user_id,
                "person_id": p.person_id,
                "provider_id": p.provider_id,
                "name": p.name,
                "relationship": p.relationship,
                "role": p.role,
                "attendance_status": "ATTENDED",
                "signature_required": p.signature_required,
            }
            for p in source_v.participants
        ]

        concerns_data = [
            {
                "concern_type": c.concern_type,
                "statement": c.statement,
                "severity": c.severity,
                "sort_order": c.sort_order,
            }
            for c in source_v.concerns
        ]

        strengths_data = [
            {
                "category": s.category,
                "statement": s.statement,
                "sort_order": s.sort_order,
            }
            for s in source_v.strengths
        ]

        goals_data = []
        for g in source_v.goals:
            if not payload.include_completed_goals and g.status == "COMPLETED":
                continue
            goals_data.append(
                {
                    "goal_text": g.goal_text,
                    "category": g.category,
                    "target_date": g.target_date,
                    "status": "NOT_STARTED" if g.status != "COMPLETED" else "COMPLETED",
                    "sort_order": g.sort_order,
                    "activities": [
                        {
                            "activity_text": a.activity_text,
                            "responsible_type": a.responsible_type,
                            "responsible_user_id": a.responsible_user_id,
                            "responsible_person_id": a.responsible_person_id,
                            "responsible_name": a.responsible_name,
                            "due_date": a.due_date,
                            "status": "NOT_STARTED" if a.status != "COMPLETED" else "COMPLETED",
                            "sort_order": a.sort_order,
                        }
                        for a in g.activities
                    ],
                }
            )

        new_plan = await self.repo.create_plan(
            case_id=source_case_id,
            primary_person_id=source_person_id,
            family_id=source_family_id,
            plan_type=source_type,
            title=title,
            meeting_date=payload.meeting_date or source_v.meeting_date,
            meeting_location=payload.meeting_location or source_v.meeting_location,
            narrative=source_v.narrative,
            created_by=user_id,
            participants=participants_data,
            concerns=concerns_data,
            strengths=strengths_data,
            goals=goals_data,
        )

        await self.timeline.record_event(
            event_type="PLAN_CLONED",
            title=f"Plan Cloned: {new_plan.plan_number}",
            description=f"Cloned from {source_plan_num} by {user_name}.",
            case_id=source_case_id,
            entity_type="plan",
            entity_id=new_plan.id,
            created_by=user_id,
        )
        await self.db.commit()
        return await self.repo.get_plan_by_id(new_plan.id)  # type: ignore

    # ── Goal & Activity Sub-Resources ─────────────────────────────────

    async def add_goal(self, user: User, plan_id: uuid.UUID, payload: PlanGoalCreate) -> PlanGoal:
        """Add a new goal with optional child activities to current plan version."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_GOAL_CREATE)

        curr_v = self._get_current_version(plan)
        if curr_v.status in ("FINALIZED", "LOCKED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot add goals to {curr_v.status} plan."
            )

        goal_id = uuid.uuid4()
        goal = PlanGoal(
            id=goal_id,
            plan_version_id=curr_v.id,
            goal_text=payload.goal_text,
            category=payload.category,
            target_date=payload.target_date,
            status=payload.status,
            sort_order=payload.sort_order,
            created_by=user_id,
        )
        self.db.add(goal)

        for idx, act in enumerate(payload.activities):
            activity = PlanActivity(
                id=uuid.uuid4(),
                goal_id=goal_id,
                activity_text=act.activity_text,
                responsible_type=act.responsible_type,
                responsible_user_id=act.responsible_user_id,
                responsible_person_id=act.responsible_person_id,
                responsible_name=act.responsible_name,
                due_date=act.due_date,
                status=act.status,
                sort_order=act.sort_order or idx,
            )
            self.db.add(activity)

        await self.db.commit()
        return await self.repo.get_goal_by_id(goal_id)  # type: ignore

    async def update_goal(self, user: User, goal_id: uuid.UUID, payload: PlanGoalUpdate) -> PlanGoal:
        """Update goal text, target date, or status."""
        user_id = user.id
        goal = await self.repo.get_goal_by_id(goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

        plan = goal.plan_version.plan
        await self._require_case_access(user_id, plan.case_id)
        await self._require_perm(user_id, Permissions.PLAN_GOAL_UPDATE)

        if goal.plan_version.status in ("FINALIZED", "LOCKED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit goal in finalized/locked plan."
            )

        if payload.goal_text is not None:
            goal.goal_text = payload.goal_text
        if payload.category is not None:
            goal.category = payload.category
        if payload.target_date is not None:
            goal.target_date = payload.target_date
        if payload.status is not None:
            goal.status = payload.status
        if payload.sort_order is not None:
            goal.sort_order = payload.sort_order

        await self.db.commit()
        return await self.repo.get_goal_by_id(goal_id)  # type: ignore

    async def complete_goal(self, user: User, goal_id: uuid.UUID, payload: PlanGoalCompleteRequest) -> PlanGoal:
        """Complete goal command endpoint."""
        user_id = user.id
        user_name = user.full_name or user.email
        goal = await self.repo.get_goal_by_id(goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

        plan = goal.plan_version.plan
        case_id = plan.case_id
        await self._require_case_access(user_id, case_id)
        await self._require_perm(user_id, Permissions.PLAN_GOAL_COMPLETE)

        goal.status = "COMPLETED"
        goal.completed_at = datetime.now(UTC)
        goal.completed_by = user_id

        if payload.notes:
            progress = GoalProgressUpdate(
                id=uuid.uuid4(),
                goal_id=goal_id,
                status="COMPLETED",
                notes=payload.notes,
                updated_by=user_id,
            )
            self.db.add(progress)

        await self.timeline.record_event(
            event_type="GOAL_COMPLETED",
            title=f"Goal Completed: {goal.goal_text[:60]}...",
            description=f"Completed by {user_name}.",
            case_id=case_id,
            entity_type="plan_goal",
            entity_id=goal.id,
            created_by=user_id,
        )

        await self.db.commit()
        return await self.repo.get_goal_by_id(goal_id)  # type: ignore

    async def add_activity(self, user: User, goal_id: uuid.UUID, payload: PlanActivityCreate) -> PlanActivity:
        """Add activity to an existing goal."""
        user_id = user.id
        goal = await self.repo.get_goal_by_id(goal_id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

        plan = goal.plan_version.plan
        await self._require_case_access(user_id, plan.case_id)
        await self._require_perm(user_id, Permissions.PLAN_ACTIVITY_CREATE)

        if goal.plan_version.status in ("FINALIZED", "LOCKED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add activities to finalized/locked plan."
            )

        act_id = uuid.uuid4()
        activity = PlanActivity(
            id=act_id,
            goal_id=goal_id,
            activity_text=payload.activity_text,
            responsible_type=payload.responsible_type,
            responsible_user_id=payload.responsible_user_id,
            responsible_person_id=payload.responsible_person_id,
            responsible_name=payload.responsible_name,
            due_date=payload.due_date,
            status=payload.status,
            sort_order=payload.sort_order,
        )
        self.db.add(activity)
        await self.db.commit()
        return await self.repo.get_activity_by_id(act_id)  # type: ignore

    async def complete_activity(
        self, user: User, activity_id: uuid.UUID, payload: PlanActivityCompleteRequest
    ) -> PlanActivity:
        """Complete an activity."""
        user_id = user.id
        activity = await self.repo.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found.")

        plan = activity.goal.plan_version.plan
        await self._require_case_access(user_id, plan.case_id)
        await self._require_perm(user_id, Permissions.PLAN_ACTIVITY_COMPLETE)

        activity.status = "COMPLETED"
        activity.completed_at = datetime.now(UTC)
        activity.completion_notes = payload.completion_notes

        await self.db.commit()
        return await self.repo.get_activity_by_id(activity_id)  # type: ignore

    # ── Signatures & Attestation ──────────────────────────────────────

    async def add_signature(self, user: User, plan_id: uuid.UUID, payload: PlanSignatureCreate) -> PlanSignature:
        """Capture and bind electronic signature to finalized plan version."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_SIGNATURE_CAPTURE)

        curr_v = self._get_current_version(plan)
        if curr_v.status not in ("FINALIZED", "LOCKED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signatures can only be captured on FINALIZED or LOCKED plans (currently {curr_v.status}).",
            )

        # 1. Cryptographic Hash Validation
        is_valid = SignatureService.verify_integrity(curr_v)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan content has changed since finalization. Signature rejected due to hash mismatch.",
            )

        sig_id = uuid.uuid4()
        sig = PlanSignature(
            id=sig_id,
            plan_version_id=curr_v.id,
            signer_type=payload.signer_type,
            signer_user_id=payload.signer_user_id or (user_id if payload.signer_type == "WORKER" else None),
            signer_person_id=payload.signer_person_id,
            signer_name=payload.signer_name,
            signer_role=payload.signer_role,
            signature_data=payload.signature_data,
            signature_image_url=payload.signature_image_url,
            signed_at=datetime.now(UTC),
            method=payload.method,
            document_hash=curr_v.document_hash,  # type: ignore
            attestation_text=payload.attestation_text
            or "I agree with this Family Wellness Plan and my commitments within it.",
            ip_address=payload.ip_address,
        )
        self.db.add(sig)

        await self.timeline.record_event(
            event_type="PLAN_SIGNED",
            title=f"Plan Signed: {payload.signer_name} ({payload.signer_role})",
            description=f"Signed {plan.plan_number} v{curr_v.version_number}. Method: {payload.method}",
            case_id=plan.case_id,
            entity_type="plan_signature",
            entity_id=sig_id,
            created_by=user_id,
        )

        await self.audit.log_event(
            event_type="PLAN_SIGNATURE_CAPTURED",
            user_id=user_id,
            entity_type="plan_signature",
            entity_id=sig_id,
            after_data={
                "plan_number": plan.plan_number,
                "signer_name": payload.signer_name,
                "role": payload.signer_role,
            },
        )

        await self.db.commit()
        return sig

    async def add_physical_signature(
        self, user: User, plan_id: uuid.UUID, payload: PhysicalSignatureUploadRequest
    ) -> PlanSignature:
        """Attach scanned physical signature document to finalized plan version."""
        user_id = user.id
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_SIGNATURE_CAPTURE)

        curr_v = self._get_current_version(plan)
        if curr_v.status not in ("FINALIZED", "LOCKED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Physical signatures can only be attached to FINALIZED or LOCKED plans (currently {curr_v.status}).",
            )

        sig_id = uuid.uuid4()
        sig = PlanSignature(
            id=sig_id,
            plan_version_id=curr_v.id,
            signer_type=payload.signer_type,
            signer_name=payload.signer_name,
            signer_role=payload.signer_role,
            signature_image_url=payload.document_url,
            signed_at=datetime.now(UTC),
            method="PHYSICAL_UPLOAD",
            document_hash=curr_v.document_hash or "PHYSICAL_SCAN_DOCUMENT",
            attestation_text=payload.notes or "Scanned physical paper document signature attached.",
        )
        self.db.add(sig)

        await self.timeline.record_event(
            event_type="PLAN_SIGNED",
            title=f"Physical Signature Uploaded: {payload.signer_name}",
            description=f"Attached paper scan for {plan.plan_number} v{curr_v.version_number}.",
            case_id=plan.case_id,
            entity_type="plan_signature",
            entity_id=sig_id,
            created_by=user_id,
        )

        await self.db.commit()
        return sig

    # ── Print View Generation ─────────────────────────────────────────

    async def get_print_data(self, user: User, plan_id: uuid.UUID) -> PlanPrintResponse:
        """Generate printable plan data with lodge headings and verified hashes."""
        user_id = user.id
        user_name = user.full_name or user.email
        plan = await self.get_plan(user, plan_id)
        await self._require_perm(user_id, Permissions.PLAN_PRINT)

        curr_v = self._get_current_version(plan)

        return PlanPrintResponse(
            plan_id=plan.id,
            plan_number=plan.plan_number,
            plan_type=plan.plan_type,
            title=plan.title,
            status=plan.status,
            version_number=curr_v.version_number,
            meeting_date=curr_v.meeting_date,
            meeting_location=curr_v.meeting_location,
            narrative=curr_v.narrative,
            document_hash=curr_v.document_hash,
            case_number=plan.case.case_number if plan.case else "N/A",
            case_title=plan.case.title if plan.case else "N/A",
            client_name=f"{plan.primary_person.first_name} {plan.primary_person.last_name}"
            if plan.primary_person
            else None,
            family_name=plan.family.family_name if plan.family else None,
            participants=[p for p in curr_v.participants],  # type: ignore
            concerns=[c for c in curr_v.concerns],  # type: ignore
            strengths=[s for s in curr_v.strengths],  # type: ignore
            goals=[g for g in curr_v.goals],  # type: ignore
            signatures=[sig for sig in curr_v.signatures],  # type: ignore
            printed_at=datetime.now(UTC),
            printed_by_name=user_name,
        )
