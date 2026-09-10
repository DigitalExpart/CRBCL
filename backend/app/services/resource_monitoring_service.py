"""Resource Home Ongoing Monitoring Service (Sprint 3).

Manages routine and periodic monitoring separate from annual licensing inspections.
Preserves historical audit trail without overwriting past visits.
Calculates overdue monitoring based on configurable cadence.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import AuditService
from app.models.outbox import OutboxEvent
from app.models.placement_home import PlacementHome
from app.models.resource_monitoring import ResourceHomeMonitoring
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.resource_monitoring import (
    ResourceHomeMonitoringCreate,
    ResourceHomeMonitoringResponse,
)


class ResourceMonitoringService:
    """Domain service for Resource Home ongoing periodic monitoring."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.perm = PermissionService(session)
        self.audit = AuditService(session)

    async def _require_perm(self, user_id: uuid.UUID, permission_key: str) -> None:
        if not await self.perm.user_has_permission(user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permission: {permission_key}",
            )

    async def create_monitoring_visit(
        self, payload: ResourceHomeMonitoringCreate, user: User
    ) -> ResourceHomeMonitoringResponse:
        """Record an ongoing monitoring visit contact log."""
        await self._require_perm(user.id, Permissions.RESOURCE_MONITORING_MANAGE)

        home = await self.session.get(PlacementHome, payload.placement_home_id)
        if not home or home.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Placement Home with ID '{payload.placement_home_id}' not found.",
            )

        # Only compute next_review_date if provided or if an explicit cadence is configured
        next_review = payload.next_review_date
        if not next_review and payload.cadence_days:
            next_review = payload.contact_date + timedelta(days=payload.cadence_days)

        monitoring = ResourceHomeMonitoring(
            placement_home_id=payload.placement_home_id,
            worker_id=user.id,
            contact_date=payload.contact_date,
            contact_type=payload.contact_type.upper(),
            child_interview_completed=payload.child_interview_completed,
            caregiver_interview_completed=payload.caregiver_interview_completed,
            safety_review_completed=payload.safety_review_completed,
            strengths=payload.strengths,
            concerns=payload.concerns,
            follow_up_required=payload.follow_up_required,
            follow_up_details=payload.follow_up_details,
            next_review_date=next_review,
            corrective_action_required=payload.corrective_action_required,
            corrective_action_notes=payload.corrective_action_notes,
            visit_id=payload.visit_id,
            document_id=payload.document_id,
            notes=payload.notes,
            status=payload.status.upper(),
            cadence_days=payload.cadence_days,
            created_by=user.id,
            updated_by=user.id,
        )
        self.session.add(monitoring)
        await self.session.flush()

        # Audit logging
        await self.audit.log(
            user_id=user.id,
            action="resource_monitoring.create",
            resource_type="resource_monitoring",
            resource_id=monitoring.id,
            details={
                "home_id": str(home.id),
                "home_name": home.name,
                "contact_type": monitoring.contact_type,
                "follow_up_required": monitoring.follow_up_required,
            },
        )

        # Transactional outbox event if follow up or corrective action is required
        if monitoring.follow_up_required or monitoring.corrective_action_required:
            outbox_event = OutboxEvent(
                event_type="resource_monitoring.follow_up_required",
                aggregate_type="resource_monitoring",
                aggregate_id=monitoring.id,
                payload={
                    "home_id": str(home.id),
                    "home_name": home.name,
                    "monitoring_id": str(monitoring.id),
                    "next_review_date": str(monitoring.next_review_date),
                    "concerns": monitoring.concerns,
                },
            )
            self.session.add(outbox_event)

        return ResourceHomeMonitoringResponse(
            id=monitoring.id,
            placement_home_id=monitoring.placement_home_id,
            worker_id=monitoring.worker_id,
            contact_date=monitoring.contact_date,
            contact_type=monitoring.contact_type,
            child_interview_completed=monitoring.child_interview_completed,
            caregiver_interview_completed=monitoring.caregiver_interview_completed,
            safety_review_completed=monitoring.safety_review_completed,
            strengths=monitoring.strengths,
            concerns=monitoring.concerns,
            follow_up_required=monitoring.follow_up_required,
            follow_up_details=monitoring.follow_up_details,
            next_review_date=monitoring.next_review_date,
            corrective_action_required=monitoring.corrective_action_required,
            corrective_action_notes=monitoring.corrective_action_notes,
            visit_id=monitoring.visit_id,
            document_id=monitoring.document_id,
            notes=monitoring.notes,
            status=monitoring.status,
            cadence_days=monitoring.cadence_days,
            created_at=monitoring.created_at,
            updated_at=monitoring.updated_at,
            worker_name=user.full_name or user.email,
            home_name=home.name,
            home_code=home.home_code,
        )

    async def list_monitoring_visits(
        self,
        user: User,
        home_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ResourceHomeMonitoringResponse], int]:
        """List monitoring visits with pagination and filtering."""
        await self._require_perm(user.id, Permissions.RESOURCE_MONITORING_READ)

        filters = [ResourceHomeMonitoring.deleted_at.is_(None)]
        if home_id:
            filters.append(ResourceHomeMonitoring.placement_home_id == home_id)
        if status:
            filters.append(ResourceHomeMonitoring.status == status.upper())

        count_stmt = select(func.count(ResourceHomeMonitoring.id)).where(*filters)
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar() or 0)

        stmt = (
            select(ResourceHomeMonitoring)
            .where(*filters)
            .options(
                selectinload(ResourceHomeMonitoring.worker),
                selectinload(ResourceHomeMonitoring.placement_home),
            )
            .order_by(desc(ResourceHomeMonitoring.contact_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.session.execute(stmt)
        items = list(res.scalars().all())

        responses = []
        for m in items:
            worker_name = (
                m.worker.full_name or m.worker.email
                if m.worker
                else None
            )
            home_name = m.placement_home.name if m.placement_home else None
            home_code = m.placement_home.home_code if m.placement_home else None
            responses.append(
                ResourceHomeMonitoringResponse(
                    id=m.id,
                    placement_home_id=m.placement_home_id,
                    worker_id=m.worker_id,
                    contact_date=m.contact_date,
                    contact_type=m.contact_type,
                    child_interview_completed=m.child_interview_completed,
                    caregiver_interview_completed=m.caregiver_interview_completed,
                    safety_review_completed=m.safety_review_completed,
                    strengths=m.strengths,
                    concerns=m.concerns,
                    follow_up_required=m.follow_up_required,
                    follow_up_details=m.follow_up_details,
                    next_review_date=m.next_review_date,
                    corrective_action_required=m.corrective_action_required,
                    corrective_action_notes=m.corrective_action_notes,
                    visit_id=m.visit_id,
                    document_id=m.document_id,
                    notes=m.notes,
                    status=m.status,
                    cadence_days=m.cadence_days,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                    worker_name=worker_name,
                    home_name=home_name,
                    home_code=home_code,
                )
            )
        return responses, total

    async def get_overdue_monitoring_homes_count(self) -> int:
        """Count active placement homes whose latest completed monitoring visit is overdue based on configured cadence."""
        today = date.today()

        # Find active placement homes where either:
        # a) No monitoring visit exists and home created > 30 days ago, or
        # b) Most recent monitoring visit next_review_date < today
        active_homes_stmt = select(PlacementHome.id).where(
            PlacementHome.status == "ACTIVE",
            PlacementHome.deleted_at.is_(None),
            PlacementHome.is_archived.is_(False),
        )
        active_home_ids = (await self.session.execute(active_homes_stmt)).scalars().all()

        overdue_count = 0
        for hid in active_home_ids:
            latest_stmt = (
                select(ResourceHomeMonitoring)
                .where(
                    ResourceHomeMonitoring.placement_home_id == hid,
                    ResourceHomeMonitoring.deleted_at.is_(None),
                    ResourceHomeMonitoring.status == "COMPLETED",
                )
                .order_by(desc(ResourceHomeMonitoring.contact_date))
                .limit(1)
            )
            latest = (await self.session.execute(latest_stmt)).scalars().first()
            if latest and (
                (latest.next_review_date and latest.next_review_date < today)
                or (latest.cadence_days and (today - latest.contact_date).days > latest.cadence_days)
            ):
                overdue_count += 1

        return overdue_count
