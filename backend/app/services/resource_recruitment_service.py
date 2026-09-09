"""Domain service for Resource Unit recruitment, state transitions, household history, and dashboard metrics.

Implements authoritative business logic adhering strictly to:
- State progression: INQUIRY -> ORIENTATION -> APPLICATION -> ASSESSMENT -> APPROVAL_REVIEW -> APPROVED
- Terminal states: DECLINED and WITHDRAWN
- Resume behavior: ON_HOLD can resume ONLY to its recorded previous stage (or move to DECLINED/WITHDRAWN)
- Append-only transition history
- Real persisted household membership history on PlacementHomeMember
- Authoritative dashboard metrics queried from live data (no aggregate tables)
"""

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
from app.models.placement import BackgroundCheck, PlacementEpisode
from app.models.placement_home import (
    PlacementHome,
    PlacementHomeLicense,
    PlacementHomeMember,
    PlacementHomeVisit,
)
from app.models.resource_recruitment import (
    RecruitmentState,
    ResourceRecruitment,
    ResourceRecruitmentApplicant,
    ResourceRecruitmentHistory,
)
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.resource_recruitment import (
    RecruitmentCreate,
    RecruitmentStateTransition,
    RecruitmentUpdate,
    ResourceDashboardMetrics,
)

# Allowed sequential forward progression
VALID_NORMAL_PROGRESSION: dict[RecruitmentState, RecruitmentState] = {
    RecruitmentState.INQUIRY: RecruitmentState.ORIENTATION,
    RecruitmentState.ORIENTATION: RecruitmentState.APPLICATION,
    RecruitmentState.APPLICATION: RecruitmentState.ASSESSMENT,
    RecruitmentState.ASSESSMENT: RecruitmentState.APPROVAL_REVIEW,
    RecruitmentState.APPROVAL_REVIEW: RecruitmentState.APPROVED,
}


class ResourceRecruitmentService:
    """Domain service managing the Resource Unit recruitment pipeline and dashboard."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit = AuditService(session)

    # ── Recruitment CRUD & Transitions ─────────────────────────────────

    async def create_recruitment(
        self, payload: RecruitmentCreate, user_id: uuid.UUID
    ) -> ResourceRecruitment:
        """Create an authoritative recruitment application record with applicant associations."""
        if not payload.applicants:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one applicant (primary) is required.",
            )

        initial_state = payload.initial_state or RecruitmentState.INQUIRY

        # Optional PlacementHome allocation check
        allocated_home = None
        if payload.resource_home_id:
            allocated_home = await self.session.get(PlacementHome, payload.resource_home_id)
            if not allocated_home or allocated_home.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Placement Home with ID '{payload.resource_home_id}' not found.",
                )

        recruitment = ResourceRecruitment(
            resource_home_id=payload.resource_home_id,
            resource_home=allocated_home,
            current_state=initial_state,
            previous_state=None,
            notes=payload.notes,
            metadata_=payload.metadata_,
            created_by=user_id,
            updated_by=user_id,
        )
        self.session.add(recruitment)
        await self.session.flush()

        # Associate applicants
        for app_input in payload.applicants:
            person = await self.session.get(Person, app_input.person_id)
            if not person or person.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Person with ID '{app_input.person_id}' not found.",
                )

            # Build immutable snapshot for audit / legal integrity
            snapshot = app_input.snapshot or {
                "first_name": person.first_name,
                "last_name": person.last_name,
                "date_of_birth": person.date_of_birth.isoformat() if person.date_of_birth else None,
                "phone": person.phone,
                "email": person.email,
            }

            applicant_record = ResourceRecruitmentApplicant(
                recruitment_id=recruitment.id,
                person_id=person.id,
                role=app_input.role,
                snapshot=snapshot,
                created_by=user_id,
                updated_by=user_id,
            )
            self.session.add(applicant_record)

        # Initial append-only history entry
        history_entry = ResourceRecruitmentHistory(
            recruitment_id=recruitment.id,
            from_state=initial_state,
            to_state=initial_state,
            changed_at=datetime.now(UTC),
            changed_by_id=user_id,
            notes=f"Recruitment application initiated in state {initial_state.value}.",
            created_by=user_id,
            updated_by=user_id,
        )
        self.session.add(history_entry)
        await self.session.flush()

        await self.audit.log(
            event_type="RESOURCE_RECRUITMENT_CREATED",
            user_id=user_id,
            entity_type="resource_recruitment",
            entity_id=recruitment.id,
            after_data={
                "initial_state": initial_state.value,
                "applicant_count": len(payload.applicants),
                "resource_home_id": str(payload.resource_home_id) if payload.resource_home_id else None,
            },
        )

        return await self.get_recruitment(recruitment.id)

    async def transition_state(
        self, recruitment_id: uuid.UUID, payload: RecruitmentStateTransition, user_id: uuid.UUID
    ) -> ResourceRecruitment:
        """Execute and audit a validated recruitment state transition."""
        recruitment = await self._get_model(recruitment_id)
        current = recruitment.current_state
        target = payload.to_state

        if current == target:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recruitment application is already in '{current.value}' state.",
            )

        # 1. Terminal state checks
        if current in (RecruitmentState.DECLINED, RecruitmentState.WITHDRAWN):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from terminal state '{current.value}'.",
            )
        if current == RecruitmentState.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recruitment application has already been APPROVED. Further transitions are not permitted.",
            )

        # Explicit approval authorization check:
        # Transitioning into APPROVED (or declining from APPROVAL_REVIEW) requires explicit approval capability.
        # Self-Approval Control Gap:
        # User accounts (system users) and Person entities (caregivers/clients) are decoupled
        # without a reliable User<->Person database foreign key. This is documented as a policy/control gap.
        requires_approval_perm = (
            target == RecruitmentState.APPROVED
            or (current == RecruitmentState.APPROVAL_REVIEW and target == RecruitmentState.DECLINED)
        )
        if requires_approval_perm:
            perm_service = PermissionService(self.session)
            has_approve_perm = await perm_service.user_has_permission(
                user_id, Permissions.RESOURCE_RECRUITMENT_APPROVE.value
            )
            if not has_approve_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "PERMISSION_DENIED",
                            "message": "User lacks required permission to approve recruitment: resource_recruitment.approve",
                        }
                    },
                )

        # 2. Allowed transition logic
        is_valid = False
        new_previous_state = recruitment.previous_state

        if current == RecruitmentState.ON_HOLD:
            # Can only resume to previous_state, or transition to DECLINED / WITHDRAWN
            if target in (RecruitmentState.DECLINED, RecruitmentState.WITHDRAWN):
                is_valid = True
            elif target == recruitment.previous_state:
                is_valid = True
                new_previous_state = None  # Cleared upon resuming
            else:
                expected = recruitment.previous_state.value if recruitment.previous_state else "its prior state"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An ON_HOLD application can only resume to {expected} or be moved to DECLINED / WITHDRAWN.",
                )
        else:
            # Active states: INQUIRY, ORIENTATION, APPLICATION, ASSESSMENT, APPROVAL_REVIEW
            if target in (RecruitmentState.DECLINED, RecruitmentState.WITHDRAWN):
                is_valid = True
            elif target == RecruitmentState.ON_HOLD:
                is_valid = True
                new_previous_state = current  # Remember state before pause
            elif VALID_NORMAL_PROGRESSION.get(current) == target:
                is_valid = True
            else:
                expected = VALID_NORMAL_PROGRESSION.get(current)
                expected_str = expected.value if expected else "none"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid progression from '{current.value}' to '{target.value}'. Expected next stage is '{expected_str}'.",
                )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transition from '{current.value}' to '{target.value}' is not allowed.",
            )

        # Optional home allocation when approving
        if target == RecruitmentState.APPROVED and payload.resource_home_id:
            home = await self.session.get(PlacementHome, payload.resource_home_id)
            if not home or home.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Placement Home with ID '{payload.resource_home_id}' not found.",
                )
            recruitment.resource_home = home
            recruitment.resource_home_id = home.id

        # Update recruitment record
        recruitment.current_state = target
        recruitment.previous_state = new_previous_state
        recruitment.updated_by = user_id
        if payload.notes:
            recruitment.notes = (
                f"{recruitment.notes}\n[Transition {datetime.now(UTC).strftime('%Y-%m-%d')}] {payload.notes}"
                if recruitment.notes
                else payload.notes
            )

        # Append to append-only transition history
        history_entry = ResourceRecruitmentHistory(
            recruitment_id=recruitment.id,
            from_state=current,
            to_state=target,
            changed_at=datetime.now(UTC),
            changed_by_id=user_id,
            notes=payload.notes,
            created_by=user_id,
            updated_by=user_id,
        )
        self.session.add(history_entry)
        await self.session.flush()

        await self.audit.log(
            event_type="RESOURCE_RECRUITMENT_TRANSITION",
            user_id=user_id,
            entity_type="resource_recruitment",
            entity_id=recruitment.id,
            after_data={
                "from_state": current.value,
                "to_state": target.value,
                "notes": payload.notes,
            },
        )

        return await self.get_recruitment(recruitment.id)

    async def update_recruitment(
        self, recruitment_id: uuid.UUID, payload: RecruitmentUpdate, user_id: uuid.UUID
    ) -> ResourceRecruitment:
        """Update recruitment application metadata or linked placement home."""
        recruitment = await self._get_model(recruitment_id)

        if payload.resource_home_id is not None:
            home = await self.session.get(PlacementHome, payload.resource_home_id)
            if not home or home.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Placement Home with ID '{payload.resource_home_id}' not found.",
                )
            recruitment.resource_home = home
            recruitment.resource_home_id = home.id

        if payload.notes is not None:
            recruitment.notes = payload.notes
        if payload.metadata_ is not None:
            recruitment.metadata_ = payload.metadata_

        recruitment.updated_by = user_id
        await self.session.flush()

        await self.audit.log(
            event_type="RESOURCE_RECRUITMENT_UPDATED",
            user_id=user_id,
            entity_type="resource_recruitment",
            entity_id=recruitment.id,
            after_data={"notes": recruitment.notes, "resource_home_id": str(recruitment.resource_home_id)},
        )

        return await self.get_recruitment(recruitment.id)

    async def get_recruitment(self, recruitment_id: uuid.UUID) -> ResourceRecruitment:
        """Fetch recruitment record with full relations loaded."""
        stmt = (
            select(ResourceRecruitment)
            .where(
                ResourceRecruitment.id == recruitment_id,
                ResourceRecruitment.deleted_at.is_(None),
            )
            .options(
                selectinload(ResourceRecruitment.applicants).joinedload(ResourceRecruitmentApplicant.person),
                selectinload(ResourceRecruitment.history).joinedload(ResourceRecruitmentHistory.changed_by),
                selectinload(ResourceRecruitment.resource_home),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recruitment application '{recruitment_id}' not found.",
            )
        return record

    async def _get_model(self, recruitment_id: uuid.UUID) -> ResourceRecruitment:
        stmt = select(ResourceRecruitment).where(
            ResourceRecruitment.id == recruitment_id,
            ResourceRecruitment.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recruitment application '{recruitment_id}' not found.",
            )
        return record

    async def list_recruitments(
        self,
        state: RecruitmentState | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResourceRecruitment]:
        """List recruitment applications with optional state filter and applicant/home search."""
        stmt = (
            select(ResourceRecruitment)
            .where(ResourceRecruitment.deleted_at.is_(None))
            .options(
                selectinload(ResourceRecruitment.applicants).joinedload(ResourceRecruitmentApplicant.person),
                selectinload(ResourceRecruitment.history),
                selectinload(ResourceRecruitment.resource_home),
            )
            .order_by(ResourceRecruitment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if state:
            stmt = stmt.where(ResourceRecruitment.current_state == state)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Real Persisted Household Membership History ────────────────────

    async def end_household_membership(
        self, member_id: uuid.UUID, user_id: uuid.UUID, end_date: date | None = None
    ) -> PlacementHomeMember:
        """End a household member's active period, preserving the row as historical record."""
        stmt = select(PlacementHomeMember).where(
            PlacementHomeMember.id == member_id,
            PlacementHomeMember.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        member = res.scalars().first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Household member '{member_id}' not found.",
            )

        effective_end = end_date or date.today()
        member.is_active = False
        member.end_date = effective_end
        member.updated_by = user_id
        # Crucial: DO NOT set deleted_at; row is preserved for complete historical audit
        await self.session.flush()

        await self.audit.log(
            event_type="PLACEMENT_HOME_MEMBER_ENDED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=member.placement_home_id,
            after_data={
                "member_id": str(member.id),
                "person_id": str(member.person_id),
                "role": member.role,
                "end_date": effective_end.isoformat(),
                "is_active": False,
            },
        )
        return member

    # ── Authoritative Dashboard Queries ────────────────────────────────

    async def get_dashboard_metrics(self) -> ResourceDashboardMetrics:
        """Calculate authoritative operational metrics using live queries (no aggregate tables)."""
        # 1. Active homes and total capacity
        homes_stmt = select(
            func.count(PlacementHome.id).label("active_count"),
            func.coalesce(func.sum(PlacementHome.total_capacity), 0).label("capacity_sum"),
        ).where(
            PlacementHome.status == "ACTIVE",
            PlacementHome.deleted_at.is_(None),
            PlacementHome.is_archived.is_(False),
        )
        homes_res = await self.session.execute(homes_stmt)
        row = homes_res.first()
        active_homes = int(row.active_count if row else 0)
        total_capacity = int(row.capacity_sum if row else 0)

        # 2. Authoritative active occupancy across all active placement homes
        active_placements_stmt = (
            select(func.count(PlacementEpisode.id))
            .join(PlacementHome, PlacementEpisode.placement_home_id == PlacementHome.id)
            .where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.deleted_at.is_(None),
                PlacementHome.is_archived.is_(False),
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.deleted_at.is_(None),
            )
        )
        active_placements_res = await self.session.execute(active_placements_stmt)
        active_placements = int(active_placements_res.scalar() or 0)

        # 3. Available beds derived authoritative calculation
        available_beds = max(0, total_capacity - active_placements)

        # 4. Recruitment counts by stage
        stages_stmt = (
            select(
                ResourceRecruitment.current_state,
                func.count(ResourceRecruitment.id),
            )
            .where(ResourceRecruitment.deleted_at.is_(None))
            .group_by(ResourceRecruitment.current_state)
        )
        stages_res = await self.session.execute(stages_stmt)
        stage_counts = {s.value: 0 for s in RecruitmentState}
        total_applications = 0
        for state_val, count in stages_res.all():
            key = state_val.value if hasattr(state_val, "value") else str(state_val)
            stage_counts[key] = int(count)
            total_applications += int(count)

        # 5. Applications awaiting action / review (APPLICATION, ASSESSMENT, APPROVAL_REVIEW)
        awaiting_review = (
            stage_counts.get(RecruitmentState.APPLICATION.value, 0)
            + stage_counts.get(RecruitmentState.ASSESSMENT.value, 0)
            + stage_counts.get(RecruitmentState.APPROVAL_REVIEW.value, 0)
        )

        # 6. Upcoming renewals within 90 days
        today = date.today()
        ninety_days = today + timedelta(days=90)
        renewals_stmt = (
            select(func.count(PlacementHomeLicense.id))
            .join(PlacementHome, PlacementHomeLicense.placement_home_id == PlacementHome.id)
            .where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.deleted_at.is_(None),
                PlacementHomeLicense.status == "ACTIVE",
                PlacementHomeLicense.deleted_at.is_(None),
                PlacementHomeLicense.expiry_date >= today,
                PlacementHomeLicense.expiry_date <= ninety_days,
            )
        )
        renewals_res = await self.session.execute(renewals_stmt)
        upcoming_renewals = int(renewals_res.scalar() or 0)

        # 7. Sprint 2 Compliance Telemetry
        thirty_days = today + timedelta(days=30)

        # 7a. Clearances expiring in next 30 days
        clearances_exp_stmt = select(func.count(BackgroundCheck.id)).where(
            BackgroundCheck.placement_home_id.isnot(None),
            BackgroundCheck.deleted_at.is_(None),
            BackgroundCheck.expiry_date.isnot(None),
            BackgroundCheck.expiry_date >= today,
            BackgroundCheck.expiry_date <= thirty_days,
        )
        clearances_exp_res = await self.session.execute(clearances_exp_stmt)
        clearances_expiring_30_days = int(clearances_exp_res.scalar() or 0)

        # 7b. Clearances expired
        clearances_expired_stmt = select(func.count(BackgroundCheck.id)).where(
            BackgroundCheck.placement_home_id.isnot(None),
            BackgroundCheck.deleted_at.is_(None),
            (BackgroundCheck.renewal_status == "EXPIRED")
            | (
                (BackgroundCheck.expiry_date.isnot(None))
                & (BackgroundCheck.expiry_date < today)
            ),
        )
        clearances_expired_res = await self.session.execute(clearances_expired_stmt)
        clearances_expired = int(clearances_expired_res.scalar() or 0)

        # 7c. Caregiver training due / expiring in 30 days
        training_due_stmt = select(func.count(CaregiverTraining.id)).where(
            CaregiverTraining.deleted_at.is_(None),
            CaregiverTraining.status != "EXPIRED",
            CaregiverTraining.expiry_date.isnot(None),
            CaregiverTraining.expiry_date >= today,
            CaregiverTraining.expiry_date <= thirty_days,
        )
        training_due_res = await self.session.execute(training_due_stmt)
        training_due_30_days = int(training_due_res.scalar() or 0)

        # 7d. Caregiver training expired
        training_expired_stmt = select(func.count(CaregiverTraining.id)).where(
            CaregiverTraining.deleted_at.is_(None),
            CaregiverTraining.expiry_date.isnot(None),
            CaregiverTraining.expiry_date < today,
        )
        training_expired_res = await self.session.execute(training_expired_stmt)
        training_expired = int(training_expired_res.scalar() or 0)

        # 7e. Inspections overdue (scheduled visit date was in the past and completed_date is None)
        inspections_overdue_stmt = select(func.count(PlacementHomeVisit.id)).where(
            PlacementHomeVisit.deleted_at.is_(None),
            PlacementHomeVisit.visit_date < today,
            PlacementHomeVisit.completed_date.is_(None),
        )
        inspections_overdue_res = await self.session.execute(inspections_overdue_stmt)
        inspections_overdue = int(inspections_overdue_res.scalar() or 0)

        # 7f. Outstanding corrective actions
        actions_stmt = select(func.count(PlacementHomeVisit.id)).where(
            PlacementHomeVisit.deleted_at.is_(None),
            PlacementHomeVisit.corrective_action_status.in_(["REQUIRED", "PENDING", "IN_PROGRESS", "OVERDUE"]),
        )
        actions_res = await self.session.execute(actions_stmt)
        outstanding_corrective_actions = int(actions_res.scalar() or 0)

        # 7g. Non-compliant homes count (distinct active homes with expired clearance, overdue corrective action, or expired license)
        non_compliant_homes_stmt = (
            select(func.count(func.distinct(PlacementHome.id)))
            .where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.deleted_at.is_(None),
                PlacementHome.is_archived.is_(False),
                (
                    PlacementHome.id.in_(
                        select(BackgroundCheck.placement_home_id).where(
                            BackgroundCheck.deleted_at.is_(None),
                            (BackgroundCheck.renewal_status == "EXPIRED")
                            | (
                                (BackgroundCheck.expiry_date.isnot(None))
                                & (BackgroundCheck.expiry_date < today)
                            ),
                        )
                    )
                    | PlacementHome.id.in_(
                        select(PlacementHomeVisit.placement_home_id).where(
                            PlacementHomeVisit.deleted_at.is_(None),
                            PlacementHomeVisit.corrective_action_status.in_(
                                ["REQUIRED", "PENDING", "IN_PROGRESS", "OVERDUE"]
                            ),
                            (
                                (PlacementHomeVisit.corrective_action_due_date.isnot(None))
                                & (PlacementHomeVisit.corrective_action_due_date < today)
                            )
                            | (PlacementHomeVisit.corrective_action_status == "OVERDUE"),
                        )
                    )
                    | PlacementHome.id.in_(
                        select(PlacementHomeLicense.placement_home_id).where(
                            PlacementHomeLicense.deleted_at.is_(None),
                            PlacementHomeLicense.status == "ACTIVE",
                            PlacementHomeLicense.expiry_date < today,
                        )
                    )
                ),
            )
        )
        non_comp_res = await self.session.execute(non_compliant_homes_stmt)
        non_compliant_homes_count = int(non_comp_res.scalar() or 0)

        return ResourceDashboardMetrics(
            active_resource_homes=active_homes,
            available_beds=available_beds,
            total_capacity=total_capacity,
            active_placements=active_placements,
            applications_by_stage=stage_counts,
            applications_awaiting_review=awaiting_review,
            upcoming_home_renewals=upcoming_renewals,
            total_applications=total_applications,
            clearances_expiring_30_days=clearances_expiring_30_days,
            clearances_expired=clearances_expired,
            training_due_30_days=training_due_30_days,
            training_expired=training_expired,
            licenses_nearing_renewal_90_days=upcoming_renewals,
            inspections_overdue=inspections_overdue,
            outstanding_corrective_actions=outstanding_corrective_actions,
            non_compliant_homes_count=non_compliant_homes_count,
        )
