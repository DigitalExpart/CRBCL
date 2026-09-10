"""Caregiver & Resource Home Supports Service (Sprint 3).

Tracks caregiver and home supports (respite, clinical, cultural, counselling, transportation)
and links financial requests to existing ServiceRequests without creating a duplicate ledger.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import AuditService
from app.models.caregiver_support import CaregiverSupport
from app.models.finance import ServiceRequest
from app.models.person import Person
from app.models.placement_home import PlacementHome
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.caregiver_support import (
    CaregiverSupportCreate,
    CaregiverSupportResponse,
    CaregiverSupportUpdate,
)


class CaregiverSupportService:
    """Domain service managing supports provided to caregivers and Resource Homes."""

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

    async def _generate_support_number(self) -> str:
        year = datetime.utcnow().year
        prefix = f"CS-{year}-"
        query = (
            select(CaregiverSupport.support_number)
            .where(CaregiverSupport.support_number.like(f"{prefix}%"))
            .order_by(desc(CaregiverSupport.support_number))
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

    async def create_support(
        self, payload: CaregiverSupportCreate, user: User
    ) -> CaregiverSupportResponse:
        """Create a new caregiver support record."""
        await self._require_perm(user.id, Permissions.CAREGIVER_SUPPORT_MANAGE)

        home = await self.session.get(PlacementHome, payload.placement_home_id)
        if not home or home.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Placement Home with ID '{payload.placement_home_id}' not found.",
            )

        caregiver = None
        if payload.caregiver_person_id:
            caregiver = await self.session.get(Person, payload.caregiver_person_id)
            if not caregiver or caregiver.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Caregiver Person with ID '{payload.caregiver_person_id}' not found.",
                )

        # Validate linked financial request if provided (link without duplication)
        if payload.service_request_id:
            sr = await self.session.get(ServiceRequest, payload.service_request_id)
            if not sr or sr.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Linked ServiceRequest with ID '{payload.service_request_id}' not found.",
                )

        support_number = await self._generate_support_number()

        support = CaregiverSupport(
            support_number=support_number,
            placement_home_id=payload.placement_home_id,
            caregiver_person_id=payload.caregiver_person_id,
            support_type=payload.support_type.upper(),
            title=payload.title,
            description=payload.description,
            requested_date=payload.requested_date,
            status="REQUESTED",
            provider_program_name=payload.provider_program_name,
            worker_id=user.id,
            frequency_duration=payload.frequency_duration,
            service_request_id=payload.service_request_id,
            amount=payload.amount,
            document_id=payload.document_id,
            created_by=user.id,
            updated_by=user.id,
        )
        self.session.add(support)
        await self.session.flush()

        await self.audit.log(
            user_id=user.id,
            action="caregiver_support.create",
            resource_type="caregiver_support",
            resource_id=support.id,
            details={
                "support_number": support_number,
                "home_id": str(home.id),
                "support_type": support.support_type,
                "amount": str(support.amount) if support.amount else None,
            },
        )

        caregiver_name = (
            f"{caregiver.first_name} {caregiver.last_name}".strip() if caregiver else None
        )
        worker_name = user.full_name or user.email

        return CaregiverSupportResponse(
            id=support.id,
            support_number=support.support_number,
            placement_home_id=support.placement_home_id,
            caregiver_person_id=support.caregiver_person_id,
            support_type=support.support_type,
            title=support.title,
            description=support.description,
            requested_date=support.requested_date,
            provided_date=support.provided_date,
            status=support.status,
            provider_program_name=support.provider_program_name,
            worker_id=support.worker_id,
            frequency_duration=support.frequency_duration,
            outcome_notes=support.outcome_notes,
            service_request_id=support.service_request_id,
            amount=support.amount,
            document_id=support.document_id,
            created_at=support.created_at,
            updated_at=support.updated_at,
            home_name=home.name,
            home_code=home.home_code,
            caregiver_name=caregiver_name,
            worker_name=worker_name,
        )

    async def list_supports(
        self,
        user: User,
        home_id: uuid.UUID | None = None,
        support_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[CaregiverSupportResponse], int]:
        """List caregiver supports with pagination and filtering."""
        await self._require_perm(user.id, Permissions.CAREGIVER_SUPPORT_READ)

        filters = [CaregiverSupport.deleted_at.is_(None)]
        if home_id:
            filters.append(CaregiverSupport.placement_home_id == home_id)
        if support_type:
            filters.append(CaregiverSupport.support_type == support_type.upper())
        if status:
            filters.append(CaregiverSupport.status == status.upper())

        count_stmt = select(func.count(CaregiverSupport.id)).where(*filters)
        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar() or 0)

        stmt = (
            select(CaregiverSupport)
            .where(*filters)
            .options(
                selectinload(CaregiverSupport.placement_home),
                selectinload(CaregiverSupport.caregiver),
                selectinload(CaregiverSupport.worker),
            )
            .order_by(desc(CaregiverSupport.requested_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.session.execute(stmt)
        supports = list(res.scalars().all())

        items = []
        for s in supports:
            caregiver_name = (
                f"{s.caregiver.first_name} {s.caregiver.last_name}".strip()
                if s.caregiver
                else None
            )
            worker_name = (s.worker.full_name or s.worker.email) if s.worker else None
            items.append(
                CaregiverSupportResponse(
                    id=s.id,
                    support_number=s.support_number,
                    placement_home_id=s.placement_home_id,
                    caregiver_person_id=s.caregiver_person_id,
                    support_type=s.support_type,
                    title=s.title,
                    description=s.description,
                    requested_date=s.requested_date,
                    provided_date=s.provided_date,
                    status=s.status,
                    provider_program_name=s.provider_program_name,
                    worker_id=s.worker_id,
                    frequency_duration=s.frequency_duration,
                    outcome_notes=s.outcome_notes,
                    service_request_id=s.service_request_id,
                    amount=s.amount,
                    document_id=s.document_id,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    home_name=s.placement_home.name if s.placement_home else None,
                    home_code=s.placement_home.home_code if s.placement_home else None,
                    caregiver_name=caregiver_name,
                    worker_name=worker_name,
                )
            )
        return items, total

    async def update_support(
        self,
        support_id: uuid.UUID,
        payload: CaregiverSupportUpdate,
        user: User,
    ) -> CaregiverSupportResponse:
        """Update caregiver support delivery status or notes."""
        await self._require_perm(user.id, Permissions.CAREGIVER_SUPPORT_MANAGE)

        support = await self.session.get(CaregiverSupport, support_id)
        if not support or support.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Caregiver support with ID '{support_id}' not found.",
            )

        if payload.status:
            support.status = payload.status.upper()
        if payload.provided_date is not None:
            support.provided_date = payload.provided_date
        if payload.outcome_notes is not None:
            support.outcome_notes = payload.outcome_notes
        if payload.frequency_duration is not None:
            support.frequency_duration = payload.frequency_duration
        if payload.amount is not None:
            support.amount = payload.amount
        if payload.service_request_id is not None:
            support.service_request_id = payload.service_request_id
        if payload.provider_program_name is not None:
            support.provider_program_name = payload.provider_program_name

        support.updated_by = user.id
        await self.session.flush()

        await self.audit.log(
            user_id=user.id,
            action="caregiver_support.update",
            resource_type="caregiver_support",
            resource_id=support.id,
            details={"status": support.status, "support_number": support.support_number},
        )

        return await self._get_response_by_id(support_id)

    async def _get_response_by_id(self, support_id: uuid.UUID) -> CaregiverSupportResponse:
        stmt = (
            select(CaregiverSupport)
            .where(CaregiverSupport.id == support_id)
            .options(
                selectinload(CaregiverSupport.placement_home),
                selectinload(CaregiverSupport.caregiver),
                selectinload(CaregiverSupport.worker),
            )
        )
        res = await self.session.execute(stmt)
        s = res.scalars().first()
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

        caregiver_name = (
            f"{s.caregiver.first_name} {s.caregiver.last_name}".strip() if s.caregiver else None
        )
        worker_name = (s.worker.full_name or s.worker.email) if s.worker else None

        return CaregiverSupportResponse(
            id=s.id,
            support_number=s.support_number,
            placement_home_id=s.placement_home_id,
            caregiver_person_id=s.caregiver_person_id,
            support_type=s.support_type,
            title=s.title,
            description=s.description,
            requested_date=s.requested_date,
            provided_date=s.provided_date,
            status=s.status,
            provider_program_name=s.provider_program_name,
            worker_id=s.worker_id,
            frequency_duration=s.frequency_duration,
            outcome_notes=s.outcome_notes,
            service_request_id=s.service_request_id,
            amount=s.amount,
            document_id=s.document_id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            home_name=s.placement_home.name if s.placement_home else None,
            home_code=s.placement_home.home_code if s.placement_home else None,
            caregiver_name=caregiver_name,
            worker_name=worker_name,
        )
