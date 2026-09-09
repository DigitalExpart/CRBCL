"""Service layer for Caregiver Training compliance and verification."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import AuditService
from app.models.caregiver_training import CaregiverTraining
from app.models.person import Person
from app.models.placement_home import PlacementHome, PlacementHomeMember
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.caregiver_training import (
    CaregiverMemberTrainingSummary,
    CaregiverTrainingCreate,
    CaregiverTrainingResponse,
    CaregiverTrainingUpdate,
    CaregiverTrainingVerify,
    HomeTrainingComplianceSummary,
)
from app.services.config_service import ConfigService
from app.workflows.outbox import OutboxService

# Training types tracked by the system across resource home types
TRACKED_TRAINING_TYPES = [
    "PRE_SERVICE_PRIDE",
    "CPR_FIRST_AID",
    "TRAUMA_INFORMED_CARE",
    "CULTURAL_SAFETY",
    "SUICIDE_PREVENTION",
    "MEDICATION_ADMINISTRATION",
]


class CaregiverTrainingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.perm_service = PermissionService(db)
        self.audit = AuditService(db)
        self.outbox = OutboxService(db)

    async def get_configured_mandatory_training_types(self) -> list[str]:
        """Retrieve training types explicitly configured as mandatory by CRBCL policy.

        Returns an empty list if not configured, preserving policy neutrality rather than
        enforcing unconfirmed universal mandatory requirements across all home types.
        """
        cfg = ConfigService(self.db)
        raw_val = await cfg.get_config_value("resource_mandatory_training_types", "")
        if not raw_val or not raw_val.strip():
            return []
        return [t.strip().upper() for t in raw_val.split(",") if t.strip()]

    async def _require_perm(self, user_id: uuid.UUID, permission_name: str) -> None:
        has_perm = await self.perm_service.user_has_permission(user_id, permission_name)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required capability: '{permission_name}'.",
            )

    async def create_training(self, user: User, data: CaregiverTrainingCreate) -> CaregiverTraining:
        await self._require_perm(user.id, Permissions.CAREGIVER_TRAINING_WRITE)

        # Verify person exists
        person = await self.db.get(Person, data.person_id)
        if not person or person.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caregiver Person not found.")

        # Verify home exists if provided
        if data.placement_home_id:
            home = await self.db.get(PlacementHome, data.placement_home_id)
            if not home or home.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement Home not found.")

        today = date.today()
        calc_status = data.status
        if data.expiry_date and data.expiry_date < today and calc_status != "WAIVED":
            calc_status = "EXPIRED"

        training = CaregiverTraining(
            person_id=data.person_id,
            placement_home_id=data.placement_home_id,
            training_type=data.training_type.upper(),
            course_name=data.course_name,
            provider_name=data.provider_name,
            completion_date=data.completion_date,
            expiry_date=data.expiry_date,
            document_id=data.document_id,
            status=calc_status,
            renewal_due_date=data.renewal_due_date or data.expiry_date,
            notes=data.notes,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(training)
        await self.db.flush()
        await self.db.refresh(training)

        await self.audit.log(
            event_type="CAREGIVER_TRAINING_RECORDED",
            user_id=user.id,
            entity_type="caregiver_training",
            entity_id=training.id,
            after_data={
                "person_id": str(training.person_id),
                "training_type": training.training_type,
                "completion_date": str(training.completion_date),
                "status": training.status,
            },
        )

        await self.outbox.enqueue(
            event_type="caregiver_training.completed",
            aggregate_type="caregiver_training",
            aggregate_id=training.id,
            payload={
                "training_id": str(training.id),
                "person_id": str(training.person_id),
                "training_type": training.training_type,
                "status": training.status,
            },
        )
        return training

    async def get_training(self, user: User, training_id: uuid.UUID) -> CaregiverTraining:
        await self._require_perm(user.id, Permissions.CAREGIVER_TRAINING_READ)
        training = await self.db.get(CaregiverTraining, training_id)
        if not training or training.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training record not found.")
        return training

    async def list_trainings(
        self,
        user: User,
        person_id: uuid.UUID | None = None,
        placement_home_id: uuid.UUID | None = None,
        status_filter: str | None = None,
        training_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[CaregiverTraining], int]:
        await self._require_perm(user.id, Permissions.CAREGIVER_TRAINING_READ)
        stmt = select(CaregiverTraining).where(CaregiverTraining.deleted_at.is_(None))

        if person_id:
            stmt = stmt.where(CaregiverTraining.person_id == person_id)
        if placement_home_id:
            stmt = stmt.where(CaregiverTraining.placement_home_id == placement_home_id)
        if status_filter:
            stmt = stmt.where(CaregiverTraining.status == status_filter.upper())
        if training_type:
            stmt = stmt.where(CaregiverTraining.training_type == training_type.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        paginated = (
            stmt.order_by(CaregiverTraining.completion_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.db.execute(paginated)
        return list(res.scalars().all()), total

    async def update_training(
        self, user: User, training_id: uuid.UUID, data: CaregiverTrainingUpdate
    ) -> CaregiverTraining:
        await self._require_perm(user.id, Permissions.CAREGIVER_TRAINING_WRITE)
        training = await self.get_training(user, training_id)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("training_type"):
            update_fields["training_type"] = update_fields["training_type"].upper()
        if update_fields.get("status"):
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(training, k, v)
        training.updated_by = user.id

        await self.audit.log(
            event_type="CAREGIVER_TRAINING_UPDATED",
            user_id=user.id,
            entity_type="caregiver_training",
            entity_id=training.id,
            after_data=update_fields,
        )
        await self.db.flush()
        return training

    async def verify_training(
        self, user: User, training_id: uuid.UUID, data: CaregiverTrainingVerify
    ) -> CaregiverTraining:
        await self._require_perm(user.id, Permissions.CAREGIVER_TRAINING_VERIFY)
        training = await self.get_training(user, training_id)

        training.status = data.status.upper()
        training.verified_by = user.id
        training.verified_at = datetime.now(UTC)
        training.updated_by = user.id
        if data.notes:
            training.notes = f"{training.notes or ''}\n[Verified by {user.full_name or user.email}]: {data.notes}".strip()

        await self.audit.log(
            event_type="CAREGIVER_TRAINING_VERIFIED",
            user_id=user.id,
            entity_type="caregiver_training",
            entity_id=training.id,
            after_data={"status": training.status, "verified_by": str(user.id)},
        )
        await self.db.flush()
        return training

    async def get_home_training_summary(self, user: User, home_id: uuid.UUID) -> HomeTrainingComplianceSummary:
        await self._require_perm(user.id, Permissions.CAREGIVER_TRAINING_READ)
        home = await self.db.get(PlacementHome, home_id)
        if not home or home.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement Home not found.")

        # Load active members
        members_stmt = (
            select(PlacementHomeMember)
            .where(
                PlacementHomeMember.placement_home_id == home_id,
                PlacementHomeMember.is_active.is_(True),
                PlacementHomeMember.deleted_at.is_(None),
            )
            .options(selectinload(PlacementHomeMember.person))
        )
        members_res = await self.db.execute(members_stmt)
        active_members = list(members_res.scalars().all())

        today = date.today()
        thirty_days_later = today + timedelta(days=30)

        member_summaries: list[CaregiverMemberTrainingSummary] = []
        compliant_caregiver_count = 0
        expiring_soon_count = 0
        expired_count = 0

        # Filter for caregivers
        caregiver_roles = {"PRIMARY_CAREGIVER", "SECONDARY_CAREGIVER", "SPOUSE_PARTNER"}
        caregiver_members = [m for m in active_members if m.role in caregiver_roles]

        configured_mandatory = await self.get_configured_mandatory_training_types()

        for m in caregiver_members:
            p_name = f"{m.person.first_name} {m.person.last_name}" if m.person else "Unknown Caregiver"

            # Query trainings for this person
            t_stmt = (
                select(CaregiverTraining)
                .where(
                    CaregiverTraining.person_id == m.person_id,
                    CaregiverTraining.deleted_at.is_(None),
                )
                .order_by(CaregiverTraining.completion_date.desc())
            )
            t_res = await self.db.execute(t_stmt)
            p_trainings = list(t_res.scalars().all())

            completed_mandatory = set()
            training_responses = []
            member_has_expired = False

            for t in p_trainings:
                is_expired = bool(t.expiry_date and t.expiry_date < today)
                is_expiring = bool(t.expiry_date and today <= t.expiry_date <= thirty_days_later)

                if is_expired:
                    expired_count += 1
                    member_has_expired = True
                elif is_expiring:
                    expiring_soon_count += 1

                if t.status in ("COMPLETED", "WAIVED") and not is_expired:
                    completed_mandatory.add(t.training_type)

                p_full_name = f"{m.person.first_name} {m.person.last_name}" if m.person else None
                training_responses.append(
                    CaregiverTrainingResponse(
                        id=t.id,
                        person_id=t.person_id,
                        person_name=p_full_name,
                        placement_home_id=t.placement_home_id,
                        placement_home_name=home.name,
                        training_type=t.training_type,
                        course_name=t.course_name,
                        provider_name=t.provider_name,
                        completion_date=t.completion_date,
                        expiry_date=t.expiry_date,
                        document_id=t.document_id,
                        status="EXPIRED" if is_expired else t.status,
                        renewal_due_date=t.renewal_due_date,
                        verified_by=t.verified_by,
                        verified_at=t.verified_at,
                        notes=t.notes,
                        created_at=t.created_at,
                        updated_at=t.updated_at,
                    )
                )

            # Policy-neutral compliance evaluation:
            # Check against configured_mandatory only. If CRBCL has not configured mandatory types,
            # missing_mandatory is empty and caregiver is compliant unless they have active expired records.
            missing_mandatory = [mt for mt in configured_mandatory if mt not in completed_mandatory]
            is_member_compliant = (len(missing_mandatory) == 0) and not member_has_expired

            if is_member_compliant:
                compliant_caregiver_count += 1

            member_summaries.append(
                CaregiverMemberTrainingSummary(
                    person_id=m.person_id,
                    person_name=p_name,
                    role=m.role,
                    trainings=training_responses,
                    mandatory_completed=sorted(list(completed_mandatory)),
                    mandatory_missing=missing_mandatory,
                    is_compliant=is_member_compliant,
                )
            )

        total_caregivers = len(caregiver_members)
        if total_caregivers == 0:
            overall_status = "COMPLIANT" if len(configured_mandatory) == 0 else "NON_COMPLIANT"
        elif compliant_caregiver_count == total_caregivers and expired_count == 0:
            overall_status = "COMPLIANT"
        elif expired_count > 0 or (len(configured_mandatory) > 0 and compliant_caregiver_count == 0):
            overall_status = "NON_COMPLIANT"
        elif len(configured_mandatory) > 0 and compliant_caregiver_count < total_caregivers:
            overall_status = "PARTIALLY_COMPLIANT"
        else:
            overall_status = "COMPLIANT"

        return HomeTrainingComplianceSummary(
            placement_home_id=home.id,
            home_code=home.home_code,
            home_name=home.name,
            overall_status=overall_status,
            total_caregivers=total_caregivers,
            compliant_caregivers=compliant_caregiver_count,
            member_summaries=member_summaries,
            expiring_soon_count=expiring_soon_count,
            expired_count=expired_count,
        )
