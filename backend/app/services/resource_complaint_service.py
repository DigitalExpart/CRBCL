"""Resource Home Complaints & Investigations Service (Sprint 3).

Implements complaint lifecycle, investigation activity logging, finalized findings immutability,
and field-level privacy redaction between basic viewers and sensitive investigators.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import AuditService
from app.models.outbox import OutboxEvent
from app.models.placement_home import PlacementHome
from app.models.resource_complaint import ResourceComplaint
from app.models.sprint_b_models import Incident
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.resource_complaint import (
    ResourceComplaintBasicResponse,
    ResourceComplaintCreate,
    ResourceComplaintDisposition,
    ResourceComplaintInvestigationUpdate,
    ResourceComplaintSensitiveResponse,
)


class ResourceComplaintService:
    """Domain service managing complaints and investigations against Resource Homes."""

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

    async def _require_any_perm(self, user_id: uuid.UUID, permission_keys: list[str]) -> None:
        perms = await self.perm.get_user_permissions(user_id)
        if not any(k in perms for k in permission_keys):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permissions: {', '.join(permission_keys)}",
            )

    async def _generate_complaint_number(self) -> str:
        year = datetime.utcnow().year
        prefix = f"RC-{year}-"
        query = (
            select(ResourceComplaint.complaint_number)
            .where(ResourceComplaint.complaint_number.like(f"{prefix}%"))
            .order_by(desc(ResourceComplaint.complaint_number))
            .limit(1)
        )
        result = await self.session.execute(query)
        last_code = result.scalar()
        if last_code:
            try:
                seq = int(last_code.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    async def create_complaint(
        self, payload: ResourceComplaintCreate, user: User
    ) -> ResourceComplaintBasicResponse:
        """Register a new complaint against a Resource Home."""
        await self._require_perm(user.id, Permissions.RESOURCE_COMPLAINT_MANAGE)

        home = await self.session.get(PlacementHome, payload.placement_home_id)
        if not home or home.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Placement Home with ID '{payload.placement_home_id}' not found.",
            )

        # Validate linked incident if provided
        if payload.incident_id:
            incident = await self.session.get(Incident, payload.incident_id)
            if not incident or incident.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Incident with ID '{payload.incident_id}' not found.",
                )

        complaint_number = await self._generate_complaint_number()
        initial_status = "ASSIGNED" if payload.assigned_investigator_id else "RECEIVED"

        complaint = ResourceComplaint(
            complaint_number=complaint_number,
            placement_home_id=payload.placement_home_id,
            complainant_category=payload.complainant_category.upper(),
            complainant_name=payload.complainant_name,
            complainant_contact=payload.complainant_contact,
            received_date=payload.received_date,
            complaint_type=payload.complaint_type.upper(),
            allegation_summary=payload.allegation_summary,
            severity=payload.severity.upper(),
            assigned_investigator_id=payload.assigned_investigator_id,
            status=initial_status,
            investigation_activities=[],
            incident_id=payload.incident_id,
            document_id=payload.document_id,
            created_by=user.id,
            updated_by=user.id,
        )
        self.session.add(complaint)
        await self.session.flush()

        # Audit complaint intake
        await self.audit.log(
            user_id=user.id,
            action="resource_complaint.create",
            resource_type="resource_complaint",
            resource_id=complaint.id,
            details={
                "complaint_number": complaint_number,
                "home_id": str(home.id),
                "severity": complaint.severity,
                "complaint_type": complaint.complaint_type,
            },
        )

        # Transactional outbox event
        outbox_event = OutboxEvent(
            event_type="resource_complaint.registered",
            aggregate_type="resource_complaint",
            aggregate_id=complaint.id,
            payload={
                "complaint_number": complaint_number,
                "home_id": str(home.id),
                "severity": complaint.severity,
                "assigned_investigator_id": str(payload.assigned_investigator_id) if payload.assigned_investigator_id else None,
            },
        )
        self.session.add(outbox_event)

        return ResourceComplaintBasicResponse(
            id=complaint.id,
            complaint_number=complaint.complaint_number,
            placement_home_id=complaint.placement_home_id,
            complainant_category=complaint.complainant_category,
            received_date=complaint.received_date,
            complaint_type=complaint.complaint_type,
            severity=complaint.severity,
            status=complaint.status,
            closure_date=complaint.closure_date,
            disposition=complaint.disposition,
            created_at=complaint.created_at,
            home_name=home.name,
            home_code=home.home_code,
        )

    async def list_complaints(
        self,
        user: User,
        home_id: uuid.UUID | None = None,
        status: str | None = None,
        severity: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ResourceComplaintBasicResponse], int]:
        """List complaints returning basic, privacy-redacted summaries."""
        await self._require_perm(user.id, Permissions.RESOURCE_COMPLAINT_READ)

        filters = [ResourceComplaint.deleted_at.is_(None)]
        if home_id:
            filters.append(ResourceComplaint.placement_home_id == home_id)
        if status:
            filters.append(ResourceComplaint.status == status.upper())
        if severity:
            filters.append(ResourceComplaint.severity == severity.upper())

        count_stmt = select(func.count(ResourceComplaint.id)).where(*filters)
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar() or 0)

        stmt = (
            select(ResourceComplaint)
            .where(*filters)
            .options(selectinload(ResourceComplaint.placement_home))
            .order_by(desc(ResourceComplaint.received_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.session.execute(stmt)
        complaints = list(res.scalars().all())

        items = [
            ResourceComplaintBasicResponse(
                id=c.id,
                complaint_number=c.complaint_number,
                placement_home_id=c.placement_home_id,
                complainant_category=c.complainant_category,
                received_date=c.received_date,
                complaint_type=c.complaint_type,
                severity=c.severity,
                status=c.status,
                closure_date=c.closure_date,
                disposition=c.disposition,
                created_at=c.created_at,
                home_name=c.placement_home.name if c.placement_home else None,
                home_code=c.placement_home.home_code if c.placement_home else None,
            )
            for c in complaints
        ]
        return items, total

    async def get_complaint_detail(
        self, complaint_id: uuid.UUID, user: User
    ) -> ResourceComplaintSensitiveResponse:
        """Fetch full sensitive details of a complaint. Requires elevated permission (investigator / supervisor / director)."""
        await self._require_any_perm(
            user.id,
            [
                Permissions.RESOURCE_COMPLAINT_SENSITIVE_READ,
                Permissions.RESOURCE_COMPLAINT_MANAGE,
                Permissions.RESOURCE_COMPLAINT_DISPOSITION,
            ],
        )

        stmt = (
            select(ResourceComplaint)
            .where(ResourceComplaint.id == complaint_id, ResourceComplaint.deleted_at.is_(None))
            .options(
                selectinload(ResourceComplaint.placement_home),
                selectinload(ResourceComplaint.investigator),
            )
        )
        res = await self.session.execute(stmt)
        c = res.scalars().first()
        if not c:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource complaint with ID '{complaint_id}' not found.",
            )

        # Audit sensitive read
        await self.audit.log(
            user_id=user.id,
            action="resource_complaint.read_sensitive",
            resource_type="resource_complaint",
            resource_id=c.id,
            details={"complaint_number": c.complaint_number},
        )

        investigator_name = (
            (c.investigator.full_name or c.investigator.email) if c.investigator else None
        )

        return ResourceComplaintSensitiveResponse(
            id=c.id,
            complaint_number=c.complaint_number,
            placement_home_id=c.placement_home_id,
            complainant_category=c.complainant_category,
            complainant_name=c.complainant_name,
            complainant_contact=c.complainant_contact,
            received_date=c.received_date,
            complaint_type=c.complaint_type,
            allegation_summary=c.allegation_summary,
            severity=c.severity,
            assigned_investigator_id=c.assigned_investigator_id,
            status=c.status,
            investigation_activities=c.investigation_activities or [],
            findings=c.findings,
            findings_finalized=c.findings_finalized,
            findings_finalized_at=c.findings_finalized_at,
            findings_finalized_by=c.findings_finalized_by,
            recommendations=c.recommendations,
            corrective_actions=c.corrective_actions,
            disposition=c.disposition,
            disposition_notes=c.disposition_notes,
            disposition_by_id=c.disposition_by_id,
            disposition_at=c.disposition_at,
            closure_date=c.closure_date,
            incident_id=c.incident_id,
            document_id=c.document_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            home_name=c.placement_home.name if c.placement_home else None,
            home_code=c.placement_home.home_code if c.placement_home else None,
            investigator_name=investigator_name,
        )

    async def update_investigation(
        self,
        complaint_id: uuid.UUID,
        payload: ResourceComplaintInvestigationUpdate,
        user: User,
    ) -> ResourceComplaintSensitiveResponse:
        """Record investigation activities and findings. Enforces immutability once findings are finalized."""
        await self._require_perm(user.id, Permissions.RESOURCE_COMPLAINT_MANAGE)

        c = await self.session.get(ResourceComplaint, complaint_id)
        if not c or c.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource complaint with ID '{complaint_id}' not found.",
            )

        # Immutability check: finalized findings cannot be overwritten
        if c.findings_finalized and payload.findings is not None and payload.findings != c.findings:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Complaint investigation findings have been finalized and are immutable.",
            )

        now = datetime.now(UTC)

        if payload.investigation_activity:
            activity = dict(payload.investigation_activity)
            activity["recorded_at"] = now.isoformat()
            activity["recorded_by"] = str(user.id)
            current_activities = list(c.investigation_activities or [])
            current_activities.append(activity)
            c.investigation_activities = current_activities

        if payload.findings is not None and not c.findings_finalized:
            c.findings = payload.findings

        if payload.finalize_findings and not c.findings_finalized:
            if not c.findings and not payload.findings:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot finalize empty findings.",
                )
            c.findings_finalized = True
            c.findings_finalized_at = now
            c.findings_finalized_by = user.id
            c.status = "FINDINGS_PENDING"

        if payload.recommendations is not None:
            c.recommendations = payload.recommendations
        if payload.corrective_actions is not None:
            c.corrective_actions = payload.corrective_actions
        if payload.status:
            c.status = payload.status.upper()

        c.updated_by = user.id
        await self.session.flush()

        await self.audit.log(
            user_id=user.id,
            action="resource_complaint.update_investigation",
            resource_type="resource_complaint",
            resource_id=c.id,
            details={
                "complaint_number": c.complaint_number,
                "findings_finalized": c.findings_finalized,
                "status": c.status,
            },
        )

        return await self.get_complaint_detail(complaint_id, user)

    async def record_disposition(
        self,
        complaint_id: uuid.UUID,
        payload: ResourceComplaintDisposition,
        user: User,
    ) -> ResourceComplaintSensitiveResponse:
        """Conclude and close complaint. Strictly requires RESOURCE_COMPLAINT_DISPOSITION (Director level)."""
        await self._require_perm(user.id, Permissions.RESOURCE_COMPLAINT_DISPOSITION)

        c = await self.session.get(ResourceComplaint, complaint_id)
        if not c or c.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource complaint with ID '{complaint_id}' not found.",
            )

        now = datetime.now(UTC)
        c.disposition = payload.disposition.upper()
        c.disposition_notes = payload.disposition_notes
        c.disposition_by_id = user.id
        c.disposition_at = now
        c.closure_date = payload.closure_date
        c.status = payload.status.upper()
        c.updated_by = user.id

        await self.session.flush()

        # Audit disposition
        await self.audit.log(
            user_id=user.id,
            action="resource_complaint.disposition",
            resource_type="resource_complaint",
            resource_id=c.id,
            details={
                "complaint_number": c.complaint_number,
                "disposition": c.disposition,
                "closure_date": str(c.closure_date),
            },
        )

        # Outbox event
        outbox_event = OutboxEvent(
            event_type="resource_complaint.disposition_recorded",
            aggregate_type="resource_complaint",
            aggregate_id=c.id,
            payload={
                "complaint_number": c.complaint_number,
                "home_id": str(c.placement_home_id),
                "disposition": c.disposition,
                "closure_date": str(c.closure_date),
            },
        )
        self.session.add(outbox_event)

        return await self.get_complaint_detail(complaint_id, user)
