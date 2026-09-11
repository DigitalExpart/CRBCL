"""Board Dashboard Service for CRBCL Governance Command Centre.

Provides strictly redacted, governance-safe aggregations and publication controls.
Zero client/case identifiers, clinical narratives, or personal details are exposed.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import AuditService
from app.models.board_action import BoardAction, BoardActionHistory
from app.models.case import Case
from app.models.department_update import DepartmentExecutiveUpdate
from app.models.executive_initiative import ExecutiveInitiative
from app.models.finance import BudgetLine, ServiceRequest
from app.models.org_ops import Employee
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.resource_recruitment import ResourceRecruitment
from app.models.sprint_b_models import FundingGrant, Incident, Program
from app.schemas.board_dashboard import (
    BoardActionHistoryItem,
    BoardActionItem,
    BoardCriticalDateItem,
    BoardDepartmentUpdateItem,
    BoardFinanceResponse,
    BoardInitiativeItem,
    BoardPerformanceResponse,
    BoardRiskItem,
    BoardRiskResponse,
    BoardSummaryMetric,
    BoardSummaryResponse,
    BoardWorkforceResponse,
)


class BoardDashboardService:
    """Service handling governance data for the CRBCL Board of Governors."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_board_summary(self, reporting_period: str | None = None) -> BoardSummaryResponse:
        """Fetch top-level governance overview metrics with zero confidential details."""
        db = self.db

        # 1. Strategic Initiatives (only board-visible)
        init_query = select(
            func.count(ExecutiveInitiative.id),
            func.count(ExecutiveInitiative.id).filter(ExecutiveInitiative.status == "ON_TRACK"),
            func.count(ExecutiveInitiative.id).filter(ExecutiveInitiative.status == "AT_RISK"),
            func.count(ExecutiveInitiative.id).filter(ExecutiveInitiative.status.in_(["DELAYED", "OVERDUE"])),
        ).where(
            ExecutiveInitiative.is_board_visible == True,  # noqa: E712
            ExecutiveInitiative.deleted_at.is_(None),
        )
        init_res = await db.execute(init_query)
        init_total, init_on_track, init_at_risk, init_delayed = init_res.one()

        # 2. Board Actions (governance-ready only)
        actions_query = select(
            func.count(BoardAction.id),
            func.count(BoardAction.id).filter(
                BoardAction.status.in_(["SUBMITTED", "UNDER_REVIEW", "DECISION_REQUIRED"])
            ),
        ).where(
            BoardAction.is_governance_ready == True,  # noqa: E712
            BoardAction.status != "DRAFT",
            BoardAction.deleted_at.is_(None),
        )
        actions_res = await db.execute(actions_query)
        actions_total, actions_pending = actions_res.one()

        # 3. High-Level Workforce
        emp_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.employment_status == "ACTIVE",
                Employee.deleted_at.is_(None),
            )
        )
        total_active_staff = emp_res.scalar() or 0

        # 4. High-Level Service Volume (distinct counts, no case data)
        children_in_care_res = await db.execute(
            select(func.count(distinct(PlacementEpisode.child_id))).where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.end_date.is_(None),
                PlacementEpisode.deleted_at.is_(None),
            )
        )
        children_in_care = children_in_care_res.scalar() or 0

        families_res = await db.execute(
            select(func.count(distinct(Case.family_id))).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.family_id.isnot(None),
                Case.deleted_at.is_(None),
            )
        )
        families_served = families_res.scalar() or 0

        # 5. Resource Home Bed Capacity
        beds_res = await db.execute(
            select(func.coalesce(func.sum(PlacementHome.total_capacity), 0)).where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.is_archived == False,  # noqa: E712
                PlacementHome.deleted_at.is_(None),
            )
        )
        total_capacity = int(beds_res.scalar() or 0)

        # 6. Approved Financial Overview (Decimal precision)
        allocated_res = await db.execute(
            select(func.coalesce(func.sum(BudgetLine.allocated_amount), Decimal("0.00"))).where(
                BudgetLine.deleted_at.is_(None)
            )
        )
        total_allocated = Decimal(str(allocated_res.scalar() or "0.00"))

        spent_res = await db.execute(
            select(func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00"))).where(
                ServiceRequest.status.in_(["APPROVED", "PAID", "COMPLETE"]),
                ServiceRequest.deleted_at.is_(None),
            )
        )
        total_spent = Decimal(str(spent_res.scalar() or "0.00"))
        total_remaining = max(Decimal("0.00"), total_allocated - total_spent)

        # 7. Major Compliance Exceptions
        today = date.today()
        expiring_licenses_res = await db.execute(
            select(func.count(PlacementHomeLicense.id)).where(
                PlacementHomeLicense.expiry_date <= today + timedelta(days=30),
                PlacementHomeLicense.status == "ACTIVE",
                PlacementHomeLicense.deleted_at.is_(None),
            )
        )
        expiring_licenses = expiring_licenses_res.scalar() or 0
        major_compliance = (init_delayed or 0) + expiring_licenses

        return BoardSummaryResponse(
            initiatives_total=init_total or 0,
            initiatives_on_track=init_on_track or 0,
            initiatives_at_risk=init_at_risk or 0,
            initiatives_delayed=init_delayed or 0,
            board_actions_pending=actions_pending or 0,
            board_actions_total=actions_total or 0,
            total_workforce=BoardSummaryMetric(value=total_active_staff, is_available=True),
            active_care_placements=BoardSummaryMetric(value=children_in_care, is_available=True),
            families_supported=BoardSummaryMetric(value=families_served, is_available=True),
            approved_bed_capacity=BoardSummaryMetric(value=total_capacity, is_available=True),
            approved_budget_total=total_allocated,
            approved_budget_spent=total_spent,
            approved_budget_remaining=total_remaining,
            major_compliance_exceptions=major_compliance,
        )

    async def get_board_actions(self, status_filter: str | None = None) -> list[BoardActionItem]:
        """Fetch governance-ready Board Actions and decision resolutions."""
        db = self.db
        stmt = (
            select(BoardAction)
            .where(
                BoardAction.is_governance_ready == True,  # noqa: E712
                BoardAction.status != "DRAFT",
                BoardAction.deleted_at.is_(None),
            )
            .options(
                selectinload(BoardAction.history).selectinload(BoardActionHistory.changed_by),
                selectinload(BoardAction.decided_by),
            )
            .order_by(BoardAction.required_by_date.asc().nulls_last(), BoardAction.created_at.desc())
        )

        if status_filter:
            stmt = stmt.where(BoardAction.status == status_filter.upper())

        res = await db.execute(stmt)
        actions = res.scalars().all()

        results = []
        for a in actions:
            history_items = [
                BoardActionHistoryItem(
                    id=h.id,
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    decision_notes=h.decision_notes,
                    action_notes=h.action_notes,
                    changed_by_name=h.changed_by.full_name if h.changed_by else None,
                    changed_at=h.changed_at,
                )
                for h in a.history
            ]

            results.append(
                BoardActionItem(
                    id=a.id,
                    reference_number=a.reference_number,
                    originating_department=a.originating_department,
                    title=a.title,
                    background_summary=a.background_summary,
                    requested_action=a.requested_action,
                    priority=a.priority,
                    required_by_date=a.required_by_date,
                    status=a.status,
                    decision=a.decision,
                    decision_date=a.decision_date,
                    decided_by_name=a.decided_by.full_name if a.decided_by else None,
                    is_governance_ready=a.is_governance_ready,
                    history=history_items,
                )
            )

        return results

    async def get_board_initiatives(self) -> list[BoardInitiativeItem]:
        """Fetch strategic initiatives approved for Board visibility."""
        db = self.db
        stmt = (
            select(ExecutiveInitiative)
            .where(
                ExecutiveInitiative.is_board_visible == True,  # noqa: E712
                ExecutiveInitiative.deleted_at.is_(None),
            )
            .order_by(ExecutiveInitiative.priority.desc(), ExecutiveInitiative.target_date.asc().nulls_last())
        )
        res = await db.execute(stmt)
        initiatives = res.scalars().all()

        return [
            BoardInitiativeItem(
                id=i.id,
                title=i.title,
                department=i.department,
                status=i.status,
                priority=i.priority,
                target_date=i.target_date,
                progress_percentage=i.progress_percentage,
                board_summary=i.board_summary or i.description,
                latest_update=i.latest_update,
                approved_for_board_at=i.approved_for_board_at,
            )
            for i in initiatives
        ]

    async def get_board_department_updates(
        self, reporting_period: str | None = None
    ) -> list[BoardDepartmentUpdateItem]:
        """Fetch department updates approved for Board review."""
        db = self.db
        stmt = (
            select(DepartmentExecutiveUpdate)
            .where(
                DepartmentExecutiveUpdate.is_board_visible == True,  # noqa: E712
                DepartmentExecutiveUpdate.deleted_at.is_(None),
            )
            .order_by(DepartmentExecutiveUpdate.reporting_period.desc(), DepartmentExecutiveUpdate.department.asc())
        )

        if reporting_period:
            stmt = stmt.where(DepartmentExecutiveUpdate.reporting_period == reporting_period)

        res = await db.execute(stmt)
        updates = res.scalars().all()

        return [
            BoardDepartmentUpdateItem(
                id=u.id,
                department=u.department,
                reporting_period=u.reporting_period,
                headline_summary=u.headline_summary,
                accomplishments_narrative=u.accomplishments_narrative,
                risks_issues=u.risks_issues,
                support_decision_requested=u.support_decision_requested,
                submitted_date=u.submitted_date,
                approved_for_board_at=u.approved_for_board_at,
            )
            for u in updates
        ]

    async def get_board_workforce(self) -> BoardWorkforceResponse:
        """Fetch aggregate workforce statistics with zero personal details."""
        db = self.db

        # Active staff
        active_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.employment_status == "ACTIVE",
                Employee.deleted_at.is_(None),
            )
        )
        total_active = active_res.scalar() or 0

        # On leave
        leave_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.employment_status == "ON_LEAVE",
                Employee.deleted_at.is_(None),
            )
        )
        total_leave = leave_res.scalar() or 0

        # Recent hires in past 30 days
        hire_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.hire_date >= (date.today() - timedelta(days=30)),
                Employee.deleted_at.is_(None),
            )
        )
        recent_hires = hire_res.scalar() or 0

        # By department
        dept_res = await db.execute(
            select(Employee.department, func.count(Employee.id))
            .where(
                Employee.employment_status == "ACTIVE",
                Employee.department.isnot(None),
                Employee.deleted_at.is_(None),
            )
            .group_by(Employee.department)
        )
        staff_by_dept = {row[0]: int(row[1]) for row in dept_res.all()}

        return BoardWorkforceResponse(
            total_active_staff=BoardSummaryMetric(value=total_active, is_available=True),
            staff_on_leave=BoardSummaryMetric(value=total_leave, is_available=True),
            recent_hires_in_period=BoardSummaryMetric(value=recent_hires, is_available=True),
            staff_by_department=staff_by_dept,
            fte_count=BoardSummaryMetric(
                value=None,
                is_available=False,
                reason="Full-Time Equivalent (FTE) allocation/hours are not tracked in current Employee schema (headcount only).",
            ),
            turnover_rate=BoardSummaryMetric(
                value=None,
                is_available=False,
                reason="Turnover rate requires authoritative separation of voluntary vs involuntary exits and historical headcount denominators, which are not tracked in current Employee schema.",
            ),
            contract_type_metric=BoardSummaryMetric(
                value=None,
                is_available=False,
                reason="HR contract type (permanent vs term) is not tracked in current Employee schema.",
            ),
            exit_reason_metric=BoardSummaryMetric(
                value=None,
                is_available=False,
                reason="Employee exit reason (resignation vs termination) is not tracked in current Employee schema.",
            ),
        )

    async def get_board_finance(self) -> BoardFinanceResponse:
        """Fetch approved aggregate finances with strict Decimal precision."""
        db = self.db

        allocated_res = await db.execute(
            select(func.coalesce(func.sum(BudgetLine.allocated_amount), Decimal("0.00"))).where(
                BudgetLine.deleted_at.is_(None)
            )
        )
        total_allocated = Decimal(str(allocated_res.scalar() or "0.00"))

        spent_res = await db.execute(
            select(func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00"))).where(
                ServiceRequest.status.in_(["APPROVED", "PAID", "COMPLETE"]),
                ServiceRequest.deleted_at.is_(None),
            )
        )
        total_spent = Decimal(str(spent_res.scalar() or "0.00"))
        total_remaining = max(Decimal("0.00"), total_allocated - total_spent)

        active_grants_res = await db.execute(
            select(func.count(FundingGrant.id)).where(
                FundingGrant.status == "ACTIVE",
                FundingGrant.deleted_at.is_(None),
            )
        )
        active_grants_count = active_grants_res.scalar() or 0

        pending_sr_res = await db.execute(
            select(
                func.count(ServiceRequest.id),
                func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00")),
            ).where(
                ServiceRequest.status.in_(["SUBMITTED", "PENDING_APPROVAL", "UNDER_REVIEW"]),
                ServiceRequest.deleted_at.is_(None),
            )
        )
        pending_row = pending_sr_res.one()
        pending_count = pending_row[0] or 0
        pending_total = Decimal(str(pending_row[1] or "0.00"))

        # Program budgets
        budget_lines_res = await db.execute(
            select(BudgetLine)
            .where(BudgetLine.deleted_at.is_(None))
            .order_by(BudgetLine.allocated_amount.desc())
            .limit(10)
        )
        budget_lines = budget_lines_res.scalars().all()
        program_budgets = [
            {
                "program_code": b.code or "PROG",
                "name": b.name,
                "allocated": Decimal(str(b.allocated_amount)),
                "spent": Decimal("0.00"),
                "remaining": Decimal(str(b.allocated_amount)),
            }
            for b in budget_lines
        ]

        return BoardFinanceResponse(
            total_allocated_budget=total_allocated,
            total_expenditure=total_spent,
            remaining_budget=total_remaining,
            active_grants_count=active_grants_count,
            pending_purchase_orders_count=pending_count,
            pending_purchase_orders_amount=pending_total,
            budget_by_program=program_budgets,
        )

    async def get_board_performance(self) -> BoardPerformanceResponse:
        """Fetch aggregate organizational performance outcomes."""
        db = self.db

        cases_res = await db.execute(
            select(func.count(Case.id)).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.deleted_at.is_(None),
            )
        )
        active_cases = cases_res.scalar() or 0

        families_res = await db.execute(
            select(func.count(distinct(Case.family_id))).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.family_id.isnot(None),
                Case.deleted_at.is_(None),
            )
        )
        families_served = families_res.scalar() or 0

        children_res = await db.execute(
            select(func.count(distinct(PlacementEpisode.child_id))).where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.end_date.is_(None),
                PlacementEpisode.deleted_at.is_(None),
            )
        )
        children_in_care = children_res.scalar() or 0

        homes_res = await db.execute(
            select(
                func.count(PlacementHome.id),
                func.coalesce(func.sum(PlacementHome.total_capacity), 0),
            ).where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.is_archived == False,  # noqa: E712
                PlacementHome.deleted_at.is_(None),
            )
        )
        homes_row = homes_res.one()
        active_homes = homes_row[0] or 0
        total_cap = int(homes_row[1] or 0)
        available_beds = max(0, total_cap - children_in_care)

        pipeline_res = await db.execute(
            select(func.count(ResourceRecruitment.id)).where(
                ResourceRecruitment.current_state.notin_(["APPROVED", "DECLINED", "WITHDRAWN"]),
                ResourceRecruitment.deleted_at.is_(None),
            )
        )
        pipeline_count = pipeline_res.scalar() or 0

        prog_res = await db.execute(
            select(
                func.count(Program.id),
                func.coalesce(func.sum(Program.enrolled_count), 0),
            ).where(
                Program.status == "ACTIVE",
                Program.deleted_at.is_(None),
            )
        )
        prog_row = prog_res.one()
        active_progs = prog_row[0] or 0
        enrolled_count = int(prog_row[1] or 0)

        return BoardPerformanceResponse(
            active_cases_total=BoardSummaryMetric(value=active_cases, is_available=True),
            families_served=BoardSummaryMetric(value=families_served, is_available=True),
            children_in_active_placements=BoardSummaryMetric(value=children_in_care, is_available=True),
            active_resource_homes=BoardSummaryMetric(value=active_homes, is_available=True),
            available_resource_beds=BoardSummaryMetric(value=available_beds, is_available=True),
            resource_recruitment_pipeline=BoardSummaryMetric(value=pipeline_count, is_available=True),
            active_cultural_programs=BoardSummaryMetric(value=active_progs, is_available=True),
            cultural_program_enrollment=BoardSummaryMetric(value=enrolled_count, is_available=True),
        )

    async def get_board_risk_compliance(self) -> BoardRiskResponse:
        """Fetch high-level organizational compliance exceptions and serious incident counts."""
        db = self.db
        today = date.today()

        # Delayed initiatives count
        delayed_res = await db.execute(
            select(func.count(ExecutiveInitiative.id)).where(
                ExecutiveInitiative.is_board_visible == True,  # noqa: E712
                ExecutiveInitiative.status.in_(["DELAYED", "OVERDUE", "AT_RISK"]),
                ExecutiveInitiative.deleted_at.is_(None),
            )
        )
        delayed_count = delayed_res.scalar() or 0

        # Expiring licenses
        exp_res = await db.execute(
            select(func.count(PlacementHomeLicense.id)).where(
                PlacementHomeLicense.expiry_date <= today + timedelta(days=30),
                PlacementHomeLicense.status == "ACTIVE",
                PlacementHomeLicense.deleted_at.is_(None),
            )
        )
        exp_count = exp_res.scalar() or 0

        # Incidents by severity (counts only, no narrative)
        inc_res = await db.execute(
            select(Incident.severity, func.count(Incident.id))
            .where(Incident.deleted_at.is_(None))
            .group_by(Incident.severity)
        )
        by_severity = {row[0]: int(row[1]) for row in inc_res.all()}
        total_incidents = sum(by_severity.values())

        # Compile risk items
        risk_items: list[BoardRiskItem] = []

        # Delayed initiatives as risk items
        init_items_res = await db.execute(
            select(ExecutiveInitiative)
            .where(
                ExecutiveInitiative.is_board_visible == True,  # noqa: E712
                ExecutiveInitiative.status.in_(["DELAYED", "AT_RISK"]),
                ExecutiveInitiative.deleted_at.is_(None),
            )
            .limit(5)
        )
        for i in init_items_res.scalars().all():
            risk_items.append(
                BoardRiskItem(
                    category="STRATEGIC_INITIATIVE",
                    title=f"{i.title} ({i.department or 'General'})",
                    severity=i.priority,
                    status=i.status,
                    due_date=i.target_date,
                )
            )

        return BoardRiskResponse(
            delayed_initiatives_count=delayed_count,
            expiring_licenses_30d_count=exp_count,
            serious_incidents_total=total_incidents,
            serious_incidents_by_severity=by_severity,
            risk_items=risk_items,
        )

    async def get_board_critical_dates(self) -> list[BoardCriticalDateItem]:
        """Fetch governance deadlines (board actions, initiative milestones).

        Strictly excludes client court appearances, family visits, or clinical appointments.
        """
        db = self.db
        today = date.today()
        dates: list[BoardCriticalDateItem] = []

        # 1. Board Action required-by dates
        actions_res = await db.execute(
            select(BoardAction)
            .where(
                BoardAction.is_governance_ready == True,  # noqa: E712
                BoardAction.required_by_date.isnot(None),
                BoardAction.status.in_(["SUBMITTED", "UNDER_REVIEW", "DECISION_REQUIRED"]),
                BoardAction.deleted_at.is_(None),
            )
            .order_by(BoardAction.required_by_date.asc())
            .limit(10)
        )
        for a in actions_res.scalars().all():
            if not a.required_by_date:
                continue
            urgency = "OVERDUE" if a.required_by_date < today else (
                "URGENT" if a.required_by_date <= today + timedelta(days=7) else "NORMAL"
            )
            dates.append(
                BoardCriticalDateItem(
                    id=str(a.id),
                    title=f"Board Decision Required: {a.title}",
                    event_type="BOARD_ACTION_DEADLINE",
                    date=a.required_by_date,
                    urgency=urgency,
                    department=a.originating_department,
                    reference_number=a.reference_number,
                )
            )

        # 2. Board-visible Initiative target dates
        init_res = await db.execute(
            select(ExecutiveInitiative)
            .where(
                ExecutiveInitiative.is_board_visible == True,  # noqa: E712
                ExecutiveInitiative.target_date.isnot(None),
                ExecutiveInitiative.status.notin_(["COMPLETED", "CANCELLED"]),
                ExecutiveInitiative.deleted_at.is_(None),
            )
            .order_by(ExecutiveInitiative.target_date.asc())
            .limit(10)
        )
        for i in init_res.scalars().all():
            if not i.target_date:
                continue
            urgency = "OVERDUE" if i.target_date < today else (
                "URGENT" if i.target_date <= today + timedelta(days=14) else "NORMAL"
            )
            dates.append(
                BoardCriticalDateItem(
                    id=str(i.id),
                    title=f"Milestone Target: {i.title}",
                    event_type="INITIATIVE_TARGET",
                    date=i.target_date,
                    urgency=urgency,
                    department=i.department,
                )
            )

        dates.sort(key=lambda d: d.date)
        return dates

    async def publish_initiative(
        self, initiative_id: uuid.UUID, is_visible: bool, board_summary: str | None, user_id: uuid.UUID
    ) -> ExecutiveInitiative | None:
        """Publish or unpublish an initiative to the Board with executive approval."""
        db = self.db
        stmt = select(ExecutiveInitiative).where(
            ExecutiveInitiative.id == initiative_id,
            ExecutiveInitiative.deleted_at.is_(None),
        )
        res = await db.execute(stmt)
        initiative = res.scalar_one_or_none()
        if not initiative:
            return None

        initiative.is_board_visible = is_visible
        if board_summary is not None:
            initiative.board_summary = board_summary

        if is_visible:
            initiative.approved_for_board_at = datetime.now(UTC)
            initiative.approved_for_board_by_id = user_id
        else:
            initiative.approved_for_board_at = None
            initiative.approved_for_board_by_id = None

        await db.flush()

        audit = AuditService(db)
        await audit.log_event(
            action="BOARD_INITIATIVE_PUBLISH" if is_visible else "BOARD_INITIATIVE_UNPUBLISH",
            resource_type="executive_initiative",
            resource_id=initiative.id,
            user_id=user_id,
            details={
                "title": initiative.title,
                "is_board_visible": is_visible,
                "board_summary": initiative.board_summary,
            },
        )
        await db.commit()
        return initiative

    async def publish_department_update(
        self, update_id: uuid.UUID, is_visible: bool, user_id: uuid.UUID
    ) -> DepartmentExecutiveUpdate | None:
        """Publish or unpublish a department executive update to the Board."""
        db = self.db
        stmt = select(DepartmentExecutiveUpdate).where(
            DepartmentExecutiveUpdate.id == update_id,
            DepartmentExecutiveUpdate.deleted_at.is_(None),
        )
        res = await db.execute(stmt)
        update = res.scalar_one_or_none()
        if not update:
            return None

        update.is_board_visible = is_visible
        if is_visible:
            update.approved_for_board_at = datetime.now(UTC)
            update.approved_for_board_by_id = user_id
        else:
            update.approved_for_board_at = None
            update.approved_for_board_by_id = None

        await db.flush()

        audit = AuditService(db)
        await audit.log_event(
            action="BOARD_DEPARTMENT_UPDATE_PUBLISH" if is_visible else "BOARD_DEPARTMENT_UPDATE_UNPUBLISH",
            resource_type="department_executive_update",
            resource_id=update.id,
            user_id=user_id,
            details={
                "department": update.department,
                "reporting_period": update.reporting_period,
                "is_board_visible": is_visible,
            },
        )
        await db.commit()
        return update

    async def record_board_decision(
        self,
        action_id: uuid.UUID,
        decision: str,
        status: str,
        resolution_notes: str | None,
        user_id: uuid.UUID,
    ) -> BoardAction | None:
        """Record formal Board decision on a BoardAction with immutable history."""
        db = self.db
        stmt = (
            select(BoardAction)
            .where(BoardAction.id == action_id, BoardAction.deleted_at.is_(None))
            .options(selectinload(BoardAction.history))
        )
        res = await db.execute(stmt)
        action = res.scalar_one_or_none()
        if not action:
            return None

        prev_status = action.status
        action.status = status.upper()
        action.decision = decision
        action.decision_date = datetime.now(UTC)
        action.decided_by_id = user_id

        # Non-destructive audit history
        history = BoardActionHistory(
            board_action=action,
            board_action_id=action.id,
            previous_status=prev_status,
            new_status=action.status,
            decision_notes=decision,
            action_notes=resolution_notes,
            changed_by_id=user_id,
        )
        if action.history is None:
            action.history = [history]
        else:
            action.history.append(history)
        db.add(history)
        await db.flush()

        audit = AuditService(db)
        await audit.log_event(
            action="BOARD_DECISION_RECORD",
            resource_type="board_action",
            resource_id=action.id,
            user_id=user_id,
            details={
                "reference_number": action.reference_number,
                "previous_status": prev_status,
                "new_status": action.status,
                "decision": decision,
            },
        )
        await db.commit()
        return action

    async def set_action_governance_ready(
        self,
        action_id: uuid.UUID,
        is_governance_ready: bool,
        user_id: uuid.UUID,
    ) -> BoardAction | None:
        """Explicitly approve or revoke BoardAction governance readiness with audit log."""
        db = self.db
        stmt = select(BoardAction).where(BoardAction.id == action_id, BoardAction.deleted_at.is_(None))
        res = await db.execute(stmt)
        action = res.scalar_one_or_none()
        if not action:
            return None

        action.is_governance_ready = is_governance_ready
        action.updated_by = user_id
        action.updated_at = datetime.now(UTC)

        audit = AuditService(db)
        await audit.log_event(
            action="BOARD_ACTION_GOVERNANCE_READY_SET",
            resource_type="board_action",
            resource_id=action.id,
            user_id=user_id,
            details={
                "reference_number": action.reference_number,
                "is_governance_ready": is_governance_ready,
            },
        )
        await db.commit()
        return action
