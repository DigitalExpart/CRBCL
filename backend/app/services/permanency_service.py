"""Service for Permanency Plans and Visitation / Family Contact Plans."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.placement import PermanencyPlan, VisitationPlan
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.placement_repo import PlacementRepository
from app.schemas.placement import (
    PermanencyPlanCreate,
    PermanencyPlanUpdate,
    VisitationPlanCreate,
    VisitationPlanUpdate,
)
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class PermanencyService:
    """Business logic for Permanency and Visitation Plans."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlacementRepository(db)
        self.perm = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def _require_case_access(self, user_id: uuid.UUID, case_id: uuid.UUID) -> None:
        if await self.perm.is_user_restricted_from_case(user_id, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

    async def _require_perm(self, user_id: uuid.UUID, permission_key: str) -> None:
        if not await self.perm.user_has_permission(user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permission: {permission_key}",
            )

    # ── Permanency Plans ─────────────────────────────────────────────
    async def create_permanency_plan(
        self, user: User, case_id: uuid.UUID, data: PermanencyPlanCreate
    ) -> PermanencyPlan:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.PERMANENCY_WRITE)

        plan = PermanencyPlan(
            case_id=case_id,
            child_id=data.child_id,
            primary_goal=data.primary_goal.upper(),
            concurrent_goal=data.concurrent_goal.upper() if data.concurrent_goal else None,
            target_date=data.target_date,
            status="DRAFT",
            cultural_heritage_strategy=data.cultural_heritage_strategy,
            sibling_co_placement_strategy=data.sibling_co_placement_strategy,
            review_frequency_months=data.review_frequency_months,
            next_review_date=data.next_review_date,
            notes=data.notes,
            established_by=user.id,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_permanency_plan(plan)

        await self.audit.log(
            event_type="PERMANENCY_PLAN_CREATED",
            user_id=user.id,
            entity_type="permanency_plan",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "primary_goal": created.primary_goal,
            },
        )
        await self.timeline.record_event(
            event_type="PERMANENCY_PLAN_ESTABLISHED",
            title=f"Permanency Plan: {created.primary_goal}",
            description=f"Permanency plan established. Primary Goal: {created.primary_goal}, Target Date: {created.target_date or 'N/A'}.",
            entity_type="permanency_plan",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="permanency_plan.created",
            aggregate_type="permanency_plan",
            aggregate_id=created.id,
            payload={
                "plan_id": str(created.id),
                "case_id": str(case_id),
                "primary_goal": created.primary_goal,
            },
        )
        return created

    async def get_permanency_plan(self, user: User, plan_id: uuid.UUID) -> PermanencyPlan:
        plan = await self.repo.get_permanency_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permanency plan not found.")
        await self._require_case_access(user.id, plan.case_id)
        await self._require_perm(user.id, Permissions.PERMANENCY_READ)
        return plan

    async def list_permanency_plans_by_case(
        self, user: User, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[PermanencyPlan], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.PERMANENCY_READ)
        return await self.repo.list_permanency_plans_by_case(case_id, page=page, page_size=page_size)

    async def update_permanency_plan(
        self, user: User, plan_id: uuid.UUID, data: PermanencyPlanUpdate
    ) -> PermanencyPlan:
        plan = await self.repo.get_permanency_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permanency plan not found.")
        await self._require_case_access(user.id, plan.case_id)
        await self._require_perm(user.id, Permissions.PERMANENCY_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if "primary_goal" in update_fields and update_fields["primary_goal"]:
            update_fields["primary_goal"] = update_fields["primary_goal"].upper()
        if "concurrent_goal" in update_fields and update_fields["concurrent_goal"]:
            update_fields["concurrent_goal"] = update_fields["concurrent_goal"].upper()
        if "status" in update_fields and update_fields["status"]:
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(plan, k, v)
        plan.updated_by = user.id
        plan.version += 1

        await self.audit.log(
            event_type="PERMANENCY_PLAN_UPDATED",
            user_id=user.id,
            entity_type="permanency_plan",
            entity_id=plan.id,
            after_data=update_fields,
        )
        return plan

    # ── Visitation Plans ─────────────────────────────────────────────
    async def create_visitation_plan(
        self, user: User, case_id: uuid.UUID, data: VisitationPlanCreate
    ) -> VisitationPlan:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.VISITATION_WRITE)

        plan = VisitationPlan(
            case_id=case_id,
            child_id=data.child_id,
            participant_names=data.participant_names,
            frequency=data.frequency.upper(),
            duration_hours=data.duration_hours,
            supervision_required=data.supervision_required,
            supervisor_type=data.supervisor_type.upper(),
            location=data.location,
            conditions=data.conditions,
            status="ACTIVE",
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            notes=data.notes,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_visitation_plan(plan)

        await self.audit.log(
            event_type="VISITATION_PLAN_CREATED",
            user_id=user.id,
            entity_type="visitation_plan",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "frequency": created.frequency,
            },
        )
        await self.timeline.record_event(
            event_type="VISITATION_SCHEDULED",
            title=f"Visitation Plan Established ({created.frequency})",
            description=f"Visitation schedule created: {created.frequency}, Supervision: {created.supervisor_type}.",
            entity_type="visitation_plan",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="visitation_plan.created",
            aggregate_type="visitation_plan",
            aggregate_id=created.id,
            payload={
                "plan_id": str(created.id),
                "case_id": str(case_id),
                "frequency": created.frequency,
            },
        )
        return created

    async def get_visitation_plan(self, user: User, plan_id: uuid.UUID) -> VisitationPlan:
        plan = await self.repo.get_visitation_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitation plan not found.")
        await self._require_case_access(user.id, plan.case_id)
        await self._require_perm(user.id, Permissions.VISITATION_READ)
        return plan

    async def list_visitation_plans_by_case(
        self, user: User, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[VisitationPlan], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.VISITATION_READ)
        return await self.repo.list_visitation_plans_by_case(case_id, page=page, page_size=page_size)

    async def update_visitation_plan(
        self, user: User, plan_id: uuid.UUID, data: VisitationPlanUpdate
    ) -> VisitationPlan:
        plan = await self.repo.get_visitation_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitation plan not found.")
        await self._require_case_access(user.id, plan.case_id)
        await self._require_perm(user.id, Permissions.VISITATION_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if "frequency" in update_fields and update_fields["frequency"]:
            update_fields["frequency"] = update_fields["frequency"].upper()
        if "supervisor_type" in update_fields and update_fields["supervisor_type"]:
            update_fields["supervisor_type"] = update_fields["supervisor_type"].upper()
        if "status" in update_fields and update_fields["status"]:
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(plan, k, v)
        plan.updated_by = user.id
        plan.version += 1

        await self.audit.log(
            event_type="VISITATION_PLAN_UPDATED",
            user_id=user.id,
            entity_type="visitation_plan",
            entity_id=plan.id,
            after_data=update_fields,
        )
        return plan
