"""CEO Dashboard aggregation service and executive governance management."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board_action import BoardAction, BoardActionHistory
from app.models.case import Case
from app.models.department_update import DepartmentExecutiveUpdate, DepartmentExecutiveUpdateHistory
from app.models.executive_initiative import (
    ExecutiveInitiative,
    ExecutiveInitiativeHistory,
)
from app.models.finance import BudgetLine, ServiceRequest
from app.models.org_ops import Employee, EmployeeCertification, FacilityWorkOrder
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.reporting_qa import QAAudit
from app.models.resource_recruitment import ResourceRecruitment
from app.models.sprint_b_models import FundingGrant, Incident, Program
from app.schemas.ceo_dashboard import (
    BoardActionCreate,
    BoardActionDecisionRequest,
    BoardActionHistoryResponse,
    BoardActionResponse,
    BoardActionUpdate,
    BudgetLineSummary,
    CeoDashboardFullResponse,
    CeoExecutiveSummary,
    ComplianceRiskItem,
    ComplianceRiskResponse,
    CriticalDateItem,
    DepartmentExecutiveUpdateCreate,
    DepartmentExecutiveUpdateResponse,
    DepartmentHealthSummary,
    ExecutiveInitiativeCreate,
    ExecutiveInitiativeHistoryResponse,
    ExecutiveInitiativeResponse,
    ExecutiveInitiativeUpdate,
    FinanceFundingResponse,
    MeasurableMetric,
    ServiceDeliveryResponse,
    WorkforceMetricsResponse,
)


def _history_sort_key(x: Any) -> tuple[float, str]:
    dt = getattr(x, "changed_at", None)
    if dt is None:
        ts = 0.0
    elif dt.tzinfo is not None:
        ts = dt.timestamp()
    else:
        ts = dt.replace(tzinfo=UTC).timestamp()
    return (ts, str(getattr(x, "id", "")))

CANONICAL_DEPARTMENTS = [
    {"code": "Resource Team", "name": "Resource Team", "metric_label": "Active Homes"},
    {"code": "Growing Up Well (Protection Services)", "name": "Growing Up Well (Protection)", "metric_label": "Active Cases"},
    {"code": "Enhancement & Preservation (Prevention Services)", "name": "Enhancement & Preservation", "metric_label": "Families Supported"},
    {"code": "Post-Majority (Young Adults)", "name": "Post-Majority", "metric_label": "Active Clients"},
    {"code": "Culture & Traditional Healing", "name": "Culture & Healing", "metric_label": "Active Programs"},
    {"code": "Early Learning / Daycare", "name": "Early Learning / Daycare", "metric_label": "Children Enrolled"},
    {"code": "Sacred Wolf Lodge", "name": "Sacred Wolf Lodge", "metric_label": "Facility Occupancy"},
    {"code": "Policy & Data", "name": "Policy & Data", "metric_label": "Active Policies"},
    {"code": "Finance & Administration", "name": "Finance & Admin", "metric_label": "Active Grants"},
    {"code": "Human Resources", "name": "Human Resources", "metric_label": "Active Staff"},
    {"code": "Operations & Facilities", "name": "Operations & Facilities", "metric_label": "Open Work Orders"},
    {"code": "Housing (Home Fire)", "name": "Housing (Home Fire)", "metric_label": "Housing Units"},
    {"code": "IT & Systems", "name": "IT & Systems", "metric_label": "Open Tickets"},
    {"code": "Communications", "name": "Communications", "metric_label": "Active Campaigns"},
    {"code": "Governance & Executive Leadership", "name": "Governance & Leadership", "metric_label": "Board Actions"},
]


class CeoDashboardService:
    """Provides high-level authoritative aggregations and governance operations for CEO."""

    @staticmethod
    async def get_full_dashboard(
        db: AsyncSession, reporting_period: str | None = None
    ) -> CeoDashboardFullResponse:
        today = date.today()
        if not reporting_period:
            reporting_period = today.strftime("%Y-%m")

        # Period start date for recent hires / exits calculation (default: 30 days ago or beginning of current month)
        period_start = today.replace(day=1)

        # ── 1. Workforce Aggregations ──────────────────────────────────────────
        active_staff_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.employment_status == "ACTIVE",
                Employee.deleted_at.is_(None)
            )
        )
        total_active_staff = active_staff_res.scalar() or 0

        on_leave_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.employment_status == "ON_LEAVE",
                Employee.deleted_at.is_(None)
            )
        )
        employees_on_leave = on_leave_res.scalar() or 0

        recent_hires_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.hire_date >= period_start,
                Employee.deleted_at.is_(None)
            )
        )
        recent_hires = recent_hires_res.scalar() or 0

        total_departures_res = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.employment_status == "TERMINATED",
                Employee.deleted_at.is_(None),
                or_(Employee.end_date >= period_start, Employee.end_date.isnot(None)),
            )
        )
        total_departures = total_departures_res.scalar() or 0

        # Staff by department
        dept_staff_res = await db.execute(
            select(Employee.department, func.count(Employee.id))
            .where(
                Employee.employment_status == "ACTIVE",
                Employee.deleted_at.is_(None)
            )
            .group_by(Employee.department)
        )
        staff_by_dept = {r[0]: r[1] for r in dept_staff_res.all() if r[0]}

        # Certification warnings (expiring within 30 days or expired)
        cert_warnings_res = await db.execute(
            select(func.count(EmployeeCertification.id)).where(
                EmployeeCertification.expiry_date <= today + timedelta(days=30)
            )
        )
        cert_warnings = cert_warnings_res.scalar() or 0

        workforce_metrics = WorkforceMetricsResponse(
            total_active_staff=MeasurableMetric(value=total_active_staff, is_available=True),
            permanent_staff=MeasurableMetric(
                value=None,
                is_available=False,
                reason="HR contract type (permanent vs term) is not tracked in current Employee schema",
            ),
            term_staff=MeasurableMetric(
                value=None,
                is_available=False,
                reason="HR contract type (permanent vs term) is not tracked in current Employee schema",
            ),
            employees_on_leave=MeasurableMetric(value=employees_on_leave, is_available=True),
            recent_hires=MeasurableMetric(value=recent_hires, is_available=True),
            recent_resignations=MeasurableMetric(
                value=None,
                is_available=False,
                reason="Employee exit reason (resignation vs termination) is not tracked in current Employee schema",
            ),
            recent_terminations=MeasurableMetric(
                value=None,
                is_available=False,
                reason="Employee exit reason (resignation vs termination) is not tracked in current Employee schema",
            ),
            total_departures=MeasurableMetric(value=total_departures, is_available=True),
            staff_by_department=staff_by_dept,
            certification_warnings=MeasurableMetric(value=cert_warnings, is_available=True),
        )

        # ── 2. Service Delivery & Caseload Aggregations ────────────────────────
        active_cases_res = await db.execute(
            select(func.count(Case.id)).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.deleted_at.is_(None)
            )
        )
        active_cases = active_cases_res.scalar() or 0

        families_served_res = await db.execute(
            select(func.count(func.distinct(Case.family_id))).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.family_id.isnot(None),
                Case.deleted_at.is_(None)
            )
        )
        # Defensible: only count families with at least one open/active case.
        # Do NOT fall back to total Family table count — that equates "in database" with "served".
        families_served = families_served_res.scalar() or 0

        # Children in care — distinct child count (not episodes, to avoid double-counting split placements)
        children_in_care_res = await db.execute(
            select(func.count(func.distinct(PlacementEpisode.child_id))).where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.end_date.is_(None),
                PlacementEpisode.deleted_at.is_(None)
            )
        )
        children_in_care = children_in_care_res.scalar() or 0

        # Protection cases specifically
        prot_cases_res = await db.execute(
            select(func.count(Case.id)).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.deleted_at.is_(None),
                or_(
                    Case.case_type.ilike("%protection%"),
                    Case.case_type.ilike("%cfs%"),
                    Case.case_type.is_(None),
                ),
            )
        )
        prot_cases = prot_cases_res.scalar() or 0

        # Post-Majority cases
        pm_cases_res = await db.execute(
            select(func.count(Case.id)).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.deleted_at.is_(None),
                Case.case_type.ilike("%post%majority%"),
            )
        )
        post_majority_cases = pm_cases_res.scalar() or 0

        # Prevention cases
        prev_cases_res = await db.execute(
            select(func.count(Case.id)).where(
                Case.status.in_(["OPEN", "ACTIVE", "Open", "Active"]),
                Case.deleted_at.is_(None),
                Case.case_type.ilike("%prevention%"),
            )
        )
        prevention_cases = prev_cases_res.scalar() or 0

        # Resource homes & beds
        active_homes_res = await db.execute(
            select(func.count(PlacementHome.id)).where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.is_archived == False,  # noqa: E712
                PlacementHome.deleted_at.is_(None)
            )
        )
        active_resource_homes = active_homes_res.scalar() or 0

        capacity_res = await db.execute(
            select(func.coalesce(func.sum(PlacementHome.total_capacity), 0)).where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.is_archived == False,  # noqa: E712
                PlacementHome.deleted_at.is_(None)
            )
        )
        total_capacity = int(capacity_res.scalar() or 0)
        available_beds = max(0, total_capacity - children_in_care)

        # Resource recruitment pipeline
        recruitment_pipeline_res = await db.execute(
            select(func.count(ResourceRecruitment.id)).where(
                ResourceRecruitment.current_state.notin_(["APPROVED", "DECLINED", "WITHDRAWN"]),
                ResourceRecruitment.deleted_at.is_(None)
            )
        )
        recruitment_pipeline = recruitment_pipeline_res.scalar() or 0

        # Programs
        active_programs_res = await db.execute(
            select(func.count(Program.id)).where(
                Program.status == "ACTIVE",
                Program.deleted_at.is_(None)
            )
        )
        active_programs = active_programs_res.scalar() or 0

        enrolled_res = await db.execute(
            select(func.coalesce(func.sum(Program.enrolled_count), 0)).where(
                Program.status == "ACTIVE",
                Program.deleted_at.is_(None)
            )
        )
        total_enrolled = int(enrolled_res.scalar() or 0)

        service_delivery = ServiceDeliveryResponse(
            protection_active_cases=MeasurableMetric(value=prot_cases, is_available=True),
            children_in_placement=MeasurableMetric(value=children_in_care, is_available=True),
            post_majority_clients=MeasurableMetric(value=post_majority_cases, is_available=True),
            prevention_families_supported=MeasurableMetric(value=prevention_cases, is_available=True),
            active_resource_homes=MeasurableMetric(value=active_resource_homes, is_available=True),
            available_beds=MeasurableMetric(value=available_beds, is_available=True),
            resource_recruitment_pipeline=MeasurableMetric(value=recruitment_pipeline, is_available=True),
            active_programs=MeasurableMetric(value=active_programs, is_available=True),
            total_program_enrollment=MeasurableMetric(value=total_enrolled, is_available=True),
        )

        # ── 3. Finance & Funding Aggregations (Strictly Decimal) ───────────────
        allocated_res = await db.execute(
            select(func.coalesce(func.sum(BudgetLine.allocated_amount), Decimal("0.00"))).where(
                BudgetLine.deleted_at.is_(None)
            )
        )
        total_allocated = Decimal(str(allocated_res.scalar() or "0.00"))

        spent_res = await db.execute(
            select(func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00"))).where(
                ServiceRequest.status.in_(["APPROVED", "PAID", "COMPLETE"]),
                ServiceRequest.deleted_at.is_(None)
            )
        )
        total_spent = Decimal(str(spent_res.scalar() or "0.00"))
        total_remaining = max(Decimal("0.00"), total_allocated - total_spent)

        active_grants_res = await db.execute(
            select(func.count(FundingGrant.id)).where(
                FundingGrant.status == "ACTIVE",
                FundingGrant.deleted_at.is_(None)
            )
        )
        active_grants_count = active_grants_res.scalar() or 0

        pending_sr_res = await db.execute(
            select(
                func.count(ServiceRequest.id),
                func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00")),
            ).where(
                ServiceRequest.status.in_(["SUBMITTED", "PENDING_APPROVAL", "UNDER_REVIEW"]),
                ServiceRequest.deleted_at.is_(None)
            )
        )
        pending_sr_row = pending_sr_res.one()
        pending_approvals_count = pending_sr_row[0] or 0
        pending_approvals_total = Decimal(str(pending_sr_row[1] or "0.00"))

        # Budget lines spending by program
        budget_lines_res = await db.execute(
            select(BudgetLine)
            .where(BudgetLine.deleted_at.is_(None))
            .order_by(BudgetLine.allocated_amount.desc())
            .limit(10)
        )
        spending_by_program = [
            BudgetLineSummary(
                code=bl.code,
                name=bl.name,
                allocated_amount=bl.allocated_amount,
                spent_amount=Decimal("0.00"),
                remaining_amount=bl.allocated_amount,
            )
            for bl in budget_lines_res.scalars().all()
        ]

        finance_metrics = FinanceFundingResponse(
            total_allocated=total_allocated,
            total_spent=total_spent,
            total_remaining=total_remaining,
            active_grants_count=active_grants_count,
            pending_financial_approvals_count=pending_approvals_count,
            pending_approvals_total_amount=pending_approvals_total,
            spending_by_program=spending_by_program,
        )

        # ── 4. Strategic Initiatives & History ────────────────────────────────
        initiatives_res = await db.execute(
            select(ExecutiveInitiative)
            .where(ExecutiveInitiative.deleted_at.is_(None))
            .options(
                selectinload(ExecutiveInitiative.responsible_owner),
                selectinload(ExecutiveInitiative.history).selectinload(ExecutiveInitiativeHistory.changed_by),
            )
            .order_by(ExecutiveInitiative.priority.desc(), ExecutiveInitiative.target_date.asc())
        )
        all_initiatives = initiatives_res.scalars().all()

        delayed_initiatives_count = 0
        initiatives_list: list[ExecutiveInitiativeResponse] = []
        for init in all_initiatives:
            is_overdue = (
                init.target_date is not None
                and init.target_date < today
                and init.status not in ["COMPLETED", "CANCELLED"]
            )
            if init.status in ["DELAYED", "AT_RISK"] or is_overdue:
                delayed_initiatives_count += 1

            hist_items = [
                ExecutiveInitiativeHistoryResponse(
                    id=h.id,
                    initiative_id=h.initiative_id,
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    progress_percentage=h.progress_percentage,
                    update_note=h.update_note,
                    changed_by_name=(
                        h.changed_by.full_name
                        if h.changed_by
                        else None
                    ),
                    changed_at=h.changed_at,
                )
                for h in sorted(init.history, key=_history_sort_key, reverse=True)
            ]

            initiatives_list.append(
                ExecutiveInitiativeResponse(
                    id=init.id,
                    title=init.title,
                    description=init.description,
                    department=init.department,
                    responsible_owner_id=init.responsible_owner_id,
                    responsible_owner_name=(
                        init.responsible_owner.full_name
                        if init.responsible_owner
                        else None
                    ),
                    status=init.status,
                    priority=init.priority,
                    target_date=init.target_date,
                    start_date=init.start_date,
                    completion_date=init.completion_date,
                    progress_percentage=init.progress_percentage,
                    latest_update=init.latest_update,
                    reporting_notes=init.reporting_notes,
                    is_overdue=is_overdue,
                    created_at=init.created_at,
                    updated_at=init.updated_at,
                    history=hist_items,
                )
            )

        # ── 5. Board Actions & Governance ─────────────────────────────────────
        board_actions_res = await db.execute(
            select(BoardAction)
            .where(BoardAction.deleted_at.is_(None))
            .options(
                selectinload(BoardAction.submitted_by),
                selectinload(BoardAction.decided_by),
                selectinload(BoardAction.linked_initiative),
                selectinload(BoardAction.history).selectinload(BoardActionHistory.changed_by),
            )
            .order_by(BoardAction.required_by_date.asc().nullslast(), BoardAction.created_at.desc())
        )
        all_board_actions = board_actions_res.scalars().all()

        board_actions_awaiting = 0
        board_actions_list: list[BoardActionResponse] = []
        for ba in all_board_actions:
            if ba.status in ["SUBMITTED", "UNDER_REVIEW", "DECISION_REQUIRED"]:
                board_actions_awaiting += 1

            ba_hist_items = [
                BoardActionHistoryResponse(
                    id=h.id,
                    board_action_id=h.board_action_id,
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    decision_notes=h.decision_notes,
                    action_notes=h.action_notes,
                    changed_by_name=(
                        h.changed_by.full_name
                        if h.changed_by
                        else None
                    ),
                    changed_at=h.changed_at,
                )
                for h in sorted(ba.history, key=_history_sort_key, reverse=True)
            ]

            board_actions_list.append(
                BoardActionResponse(
                    id=ba.id,
                    reference_number=ba.reference_number,
                    originating_department=ba.originating_department,
                    linked_initiative_id=ba.linked_initiative_id,
                    linked_initiative_title=(
                        ba.linked_initiative.title if ba.linked_initiative else None
                    ),
                    title=ba.title,
                    background_summary=ba.background_summary,
                    requested_action=ba.requested_action,
                    priority=ba.priority,
                    required_by_date=ba.required_by_date,
                    status=ba.status,
                    submitted_by_id=ba.submitted_by_id,
                    submitted_by_name=(
                        ba.submitted_by.full_name
                        if ba.submitted_by
                        else None
                    ),
                    submitted_date=ba.submitted_date,
                    decision=ba.decision,
                    decision_date=ba.decision_date,
                    decided_by_name=(
                        ba.decided_by.full_name
                        if ba.decided_by
                        else None
                    ),
                    is_governance_ready=ba.is_governance_ready,
                    created_at=ba.created_at,
                    updated_at=ba.updated_at,
                    history=ba_hist_items,
                )
            )

        # ── 6. Department Executive Updates ───────────────────────────────────
        dept_updates_res = await db.execute(
            select(DepartmentExecutiveUpdate)
            .where(DepartmentExecutiveUpdate.deleted_at.is_(None))
            .options(
                selectinload(DepartmentExecutiveUpdate.submitted_by),
                selectinload(DepartmentExecutiveUpdate.linked_initiative),
                selectinload(DepartmentExecutiveUpdate.linked_board_action),
            )
            .order_by(
                DepartmentExecutiveUpdate.reporting_period.desc(),
                DepartmentExecutiveUpdate.created_at.desc(),
            )
        )
        all_dept_updates = dept_updates_res.scalars().all()
        dept_updates_list = [
            DepartmentExecutiveUpdateResponse(
                id=u.id,
                reporting_period=u.reporting_period,
                department=u.department,
                submitted_by_id=u.submitted_by_id,
                submitted_by_name=(
                    u.submitted_by.full_name
                    if u.submitted_by
                    else None
                ),
                submitted_date=u.submitted_date,
                headline_summary=u.headline_summary,
                accomplishments_narrative=u.accomplishments_narrative,
                risks_issues=u.risks_issues,
                support_decision_requested=u.support_decision_requested,
                status=u.status,
                linked_initiative_id=u.linked_initiative_id,
                linked_initiative_title=(
                    u.linked_initiative.title if u.linked_initiative else None
                ),
                linked_board_action_id=u.linked_board_action_id,
                linked_board_action_title=(
                    u.linked_board_action.title if u.linked_board_action else None
                ),
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in all_dept_updates
        ]

        # ── 7. Compliance & Risk Exceptions ───────────────────────────────────
        compliance_items: list[ComplianceRiskItem] = []

        # (a) Overdue & at-risk initiatives
        for init in all_initiatives:
            if init.status == "DELAYED" or (
                init.target_date and init.target_date < today and init.status != "COMPLETED"
            ):
                compliance_items.append(
                    ComplianceRiskItem(
                        category="INITIATIVE",
                        severity="HIGH" if init.priority in ["HIGH", "CRITICAL"] else "MEDIUM",
                        title=f"Delayed Initiative: {init.title}",
                        department=init.department,
                        due_or_event_date=init.target_date,
                        details=f"Status is {init.status}. Target date was {init.target_date}.",
                        reference_id=str(init.id),
                    )
                )

        # (b) Major Incidents (SEV-1 / Critical)
        incidents_res = await db.execute(
            select(Incident).where(
                Incident.deleted_at.is_(None),
                Incident.severity.in_(["CRITICAL", "HIGH", "SEV-1", "SEV-2"]),
                Incident.status.in_(["OPEN", "UNDER_INVESTIGATION", "Open"]),
            )
        )
        for inc in incidents_res.scalars().all():
            compliance_items.append(
                ComplianceRiskItem(
                    category="INCIDENT",
                    severity="CRITICAL" if inc.severity in ["CRITICAL", "SEV-1"] else "HIGH",
                    title=f"Active Critical Incident: {inc.title}",
                    due_or_event_date=inc.created_at,
                    details=f"Incident type: {inc.incident_type}. Status: {inc.status}.",
                    reference_id=str(inc.id),
                )
            )

        # (c) Expiring Resource Home Licenses
        exp_licenses_res = await db.execute(
            select(PlacementHomeLicense).where(
                PlacementHomeLicense.expiry_date <= today + timedelta(days=30),
                PlacementHomeLicense.status.in_(["ACTIVE", "PENDING_RENEWAL", "Active"]),
            )
        )
        for lic in exp_licenses_res.scalars().all():
            compliance_items.append(
                ComplianceRiskItem(
                    category="RESOURCE",
                    severity="HIGH",
                    title=f"Expiring Home License: {lic.license_number}",
                    due_or_event_date=lic.expiry_date,
                    details=f"License expires on {lic.expiry_date}. Status: {lic.status}.",
                    reference_id=str(lic.id),
                )
            )

        # (d) Pending Board Decisions requiring action
        for ba in all_board_actions:
            if ba.status == "DECISION_REQUIRED" or (
                ba.status == "SUBMITTED" and ba.required_by_date and ba.required_by_date <= today
            ):
                compliance_items.append(
                    ComplianceRiskItem(
                        category="BOARD",
                        severity="HIGH",
                        title=f"Board Decision Required: {ba.title}",
                        department=ba.originating_department,
                        due_or_event_date=ba.required_by_date,
                        details=f"Reference {ba.reference_number}. Requested action: {ba.requested_action[:100]}...",
                        reference_id=ba.reference_number,
                    )
                )

        # (e) QA Audits exceptions
        qa_audits_res = await db.execute(
            select(QAAudit).where(
                QAAudit.deleted_at.is_(None),
                or_(
                    QAAudit.overall_score < Decimal("70.00"),
                    QAAudit.status == "IN_PROGRESS",
                ),
            ).limit(5)
        )
        for qa in qa_audits_res.scalars().all():
            compliance_items.append(
                ComplianceRiskItem(
                    category="AUDIT",
                    severity="HIGH" if (qa.overall_score and qa.overall_score < Decimal("50.00")) else "MEDIUM",
                    title=f"QA Audit Exception: Case {qa.case_id}",
                    department="Quality Assurance",
                    due_or_event_date=qa.review_date,
                    details=f"Status: {qa.status}. Score: {qa.overall_score}%.",
                    reference_id=str(qa.id),
                )
            )


        critical_count = sum(1 for item in compliance_items if item.severity == "CRITICAL")
        high_count = sum(1 for item in compliance_items if item.severity == "HIGH")

        compliance_response = ComplianceRiskResponse(
            total_exceptions=len(compliance_items),
            critical_exceptions=critical_count,
            high_exceptions=high_count,
            items=compliance_items,
        )

        # ── 8. Critical Dates Feed ────────────────────────────────────────────
        critical_dates_list: list[CriticalDateItem] = []

        # From initiatives
        for init in all_initiatives:
            if init.target_date and init.status not in ["COMPLETED", "CANCELLED"]:
                urgency = "OVERDUE" if init.target_date < today else (
                    "URGENT" if init.target_date <= today + timedelta(days=14) else "NORMAL"
                )
                critical_dates_list.append(
                    CriticalDateItem(
                        date=init.target_date,
                        title=f"Initiative Milestone: {init.title}",
                        category="INITIATIVE",
                        department=init.department,
                        urgency=urgency,
                        reference_id=str(init.id),
                    )
                )

        # From board actions
        for ba in all_board_actions:
            if ba.required_by_date and ba.status not in ["APPROVED", "RESOLVED", "DECLINED", "WITHDRAWN"]:
                urgency = "OVERDUE" if ba.required_by_date < today else (
                    "URGENT" if ba.required_by_date <= today + timedelta(days=14) else "NORMAL"
                )
                critical_dates_list.append(
                    CriticalDateItem(
                        date=ba.required_by_date,
                        title=f"Board Action Deadline: {ba.title}",
                        category="BOARD_ACTION",
                        department=ba.originating_department,
                        urgency=urgency,
                        reference_id=ba.reference_number,
                    )
                )

        critical_dates_list.sort(key=lambda x: x.date)

        # ── 9. Department Health Summaries ────────────────────────────────────
        # Work orders count for Operations
        wo_count_res = await db.execute(
            select(func.count(FacilityWorkOrder.id)).where(
                FacilityWorkOrder.status.in_(["OPEN", "IN_PROGRESS", "Open"]),
            )
        )
        open_work_orders = wo_count_res.scalar() or 0

        dept_health_list: list[DepartmentHealthSummary] = []
        for dept in CANONICAL_DEPARTMENTS:
            code = dept["code"]
            active_staff = staff_by_dept.get(code, 0)
            # Match initiatives by exact code or partial
            dept_inits = [i for i in all_initiatives if i.department == code]
            active_inits = sum(1 for i in dept_inits if i.status in ["ON_TRACK", "AT_RISK", "DELAYED"])
            delayed_inits = sum(1 for i in dept_inits if i.status in ["DELAYED", "AT_RISK"])

            # Pending board actions
            dept_bas = [
                b for b in all_board_actions
                if b.originating_department == code
                and b.status in ["SUBMITTED", "UNDER_REVIEW", "DECISION_REQUIRED"]
            ]

            # Latest department update
            dept_updates = [u for u in all_dept_updates if u.department == code]
            latest_upd = dept_updates[0] if dept_updates else None

            # Operational metric value
            op_metric_val = None
            if "Protection" in code:
                op_metric_val = str(prot_cases)
            elif "Resource" in code:
                op_metric_val = str(active_resource_homes)
            elif "Post-Majority" in code:
                op_metric_val = str(post_majority_cases)
            elif "Prevention" in code:
                op_metric_val = str(prevention_cases)
            elif "Culture" in code:
                op_metric_val = str(active_programs)
            elif "Operations" in code:
                op_metric_val = str(open_work_orders)
            elif "Finance" in code:
                op_metric_val = str(active_grants_count)
            elif "Human Resources" in code:
                op_metric_val = str(total_active_staff)

            dept_health_list.append(
                DepartmentHealthSummary(
                    department=code,
                    name=dept["name"],
                    active_staff=active_staff,
                    active_initiatives=active_inits,
                    delayed_initiatives=delayed_inits,
                    pending_board_actions=len(dept_bas),
                    has_recent_update=latest_upd is not None,
                    latest_update_period=latest_upd.reporting_period if latest_upd else None,
                    latest_update_headline=latest_upd.headline_summary if latest_upd else None,
                    operational_metric_label=dept.get("metric_label"),
                    operational_metric_value=op_metric_val,
                )
            )

        # ── 10. Top-Level CEO Executive Summary ────────────────────────────────
        exec_summary = CeoExecutiveSummary(
            total_active_employees=MeasurableMetric(value=total_active_staff, is_available=True),
            active_cases=MeasurableMetric(value=active_cases, is_available=True),
            families_served=MeasurableMetric(value=families_served, is_available=True),
            children_in_care=MeasurableMetric(value=children_in_care, is_available=True),
            active_resource_homes=MeasurableMetric(value=active_resource_homes, is_available=True),
            resource_capacity=MeasurableMetric(value=total_capacity, is_available=True),
            resource_available_beds=MeasurableMetric(value=available_beds, is_available=True),
            active_programs=MeasurableMetric(value=active_programs, is_available=True),
            major_compliance_exceptions=MeasurableMetric(
                value=compliance_response.total_exceptions, is_available=True
            ),
            delayed_overdue_initiatives=MeasurableMetric(
                value=delayed_initiatives_count, is_available=True
            ),
            board_actions_awaiting_decision=MeasurableMetric(
                value=board_actions_awaiting, is_available=True
            ),
        )

        return CeoDashboardFullResponse(
            reporting_period=reporting_period,
            executive_summary=exec_summary,
            department_health=dept_health_list,
            workforce=workforce_metrics,
            service_delivery=service_delivery,
            finance=finance_metrics,
            compliance_risk=compliance_response,
            critical_dates=critical_dates_list[:15],
            active_initiatives=initiatives_list,
            pending_board_actions=board_actions_list,
            recent_department_updates=dept_updates_list[:10],
        )

    # ── Initiatives CRUD & Audit History ──────────────────────────────────────

    @staticmethod
    async def create_initiative(
        db: AsyncSession, data: ExecutiveInitiativeCreate, current_user_id: uuid.UUID
    ) -> ExecutiveInitiative:
        init = ExecutiveInitiative(
            title=data.title,
            description=data.description,
            department=data.department,
            responsible_owner_id=data.responsible_owner_id,
            status=data.status,
            priority=data.priority,
            target_date=data.target_date,
            start_date=data.start_date,
            completion_date=data.completion_date,
            progress_percentage=data.progress_percentage,
            latest_update=data.latest_update,
            reporting_notes=data.reporting_notes,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(init)
        await db.flush()

        # Initial append-only audit log
        history_entry = ExecutiveInitiativeHistory(
            initiative_id=init.id,
            previous_status="NEW",
            new_status=init.status,
            progress_percentage=init.progress_percentage,
            update_note="Initiative created",
            changed_by_id=current_user_id,
            changed_at=datetime.now(UTC),
        )
        db.add(history_entry)
        await db.commit()
        await db.refresh(init)
        return init

    @staticmethod
    async def update_initiative(
        db: AsyncSession,
        initiative_id: uuid.UUID,
        data: ExecutiveInitiativeUpdate,
        current_user_id: uuid.UUID,
    ) -> ExecutiveInitiative:
        stmt = (
            select(ExecutiveInitiative)
            .where(
                ExecutiveInitiative.id == initiative_id,
                ExecutiveInitiative.deleted_at.is_(None)
            )
            .options(selectinload(ExecutiveInitiative.history))
        )
        res = await db.execute(stmt)
        init = res.scalar_one_or_none()
        if not init:
            raise ValueError("Initiative not found")

        prev_status = init.status
        is_status_changed = data.status is not None and data.status != prev_status
        is_progress_changed = (
            data.progress_percentage is not None
            and data.progress_percentage != init.progress_percentage
        )
        has_update_note = bool(data.status_change_note or data.latest_update)

        if data.title is not None:
            init.title = data.title
        if data.description is not None:
            init.description = data.description
        if data.department is not None:
            init.department = data.department
        if data.responsible_owner_id is not None:
            init.responsible_owner_id = data.responsible_owner_id
        if data.status is not None:
            init.status = data.status
            if data.status == "COMPLETED" and not init.completion_date:
                init.completion_date = date.today()
        if data.priority is not None:
            init.priority = data.priority
        if data.target_date is not None:
            init.target_date = data.target_date
        if data.start_date is not None:
            init.start_date = data.start_date
        if data.completion_date is not None:
            init.completion_date = data.completion_date
        if data.progress_percentage is not None:
            init.progress_percentage = data.progress_percentage
        if data.latest_update is not None:
            init.latest_update = data.latest_update
        if data.reporting_notes is not None:
            init.reporting_notes = data.reporting_notes

        init.updated_by = current_user_id
        init.updated_at = datetime.now()

        # Preserve append-only audit trail if status, progress, or update note provided
        if is_status_changed or is_progress_changed or has_update_note:
            history_entry = ExecutiveInitiativeHistory(
                initiative_id=init.id,
                previous_status=prev_status,
                new_status=init.status,
                progress_percentage=init.progress_percentage,
                update_note=data.status_change_note or data.latest_update,
                changed_by_id=current_user_id,
                changed_at=datetime.now(UTC),
            )
            db.add(history_entry)

        await db.commit()
        await db.refresh(init)
        return init

    # ── Board Actions CRUD & Governance Decisions ─────────────────────────────

    @staticmethod
    async def create_board_action(
        db: AsyncSession, data: BoardActionCreate, current_user_id: uuid.UUID
    ) -> BoardAction:
        # Generate sequence reference: BA-YYYY-XXXX
        year = datetime.now().year
        count_res = await db.execute(select(func.count(BoardAction.id)))
        next_seq = (count_res.scalar() or 0) + 1
        ref_num = f"BA-{year}-{next_seq:04d}"

        ba = BoardAction(
            reference_number=ref_num,
            originating_department=data.originating_department,
            linked_initiative_id=data.linked_initiative_id,
            title=data.title,
            background_summary=data.background_summary,
            requested_action=data.requested_action,
            priority=data.priority,
            required_by_date=data.required_by_date,
            status=data.status,
            submitted_by_id=current_user_id,
            submitted_date=datetime.now(),
            is_governance_ready=data.is_governance_ready,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(ba)
        await db.flush()

        # Audit ledger
        history_entry = BoardActionHistory(
            board_action_id=ba.id,
            previous_status="NEW",
            new_status=ba.status,
            action_notes="Board action submitted",
            changed_by_id=current_user_id,
            changed_at=datetime.now(UTC),
        )
        db.add(history_entry)
        await db.commit()
        await db.refresh(ba)
        return ba

    @staticmethod
    async def update_board_action(
        db: AsyncSession,
        action_id: uuid.UUID,
        data: BoardActionUpdate,
        current_user_id: uuid.UUID,
    ) -> BoardAction:
        stmt = (
            select(BoardAction)
            .where(
                BoardAction.id == action_id,
                BoardAction.deleted_at.is_(None)
            )
            .options(selectinload(BoardAction.history))
        )
        res = await db.execute(stmt)
        ba = res.scalar_one_or_none()
        if not ba:
            raise ValueError("Board action not found")

        prev_status = ba.status
        if data.title is not None:
            ba.title = data.title
        if data.background_summary is not None:
            ba.background_summary = data.background_summary
        if data.requested_action is not None:
            ba.requested_action = data.requested_action
        if data.priority is not None:
            ba.priority = data.priority
        if data.required_by_date is not None:
            ba.required_by_date = data.required_by_date
        if data.is_governance_ready is not None:
            ba.is_governance_ready = data.is_governance_ready
        if data.status is not None:
            ba.status = data.status
        if data.decision is not None:
            ba.decision = data.decision
            ba.decision_date = datetime.now()
            ba.decided_by_id = current_user_id

        ba.updated_by = current_user_id
        ba.updated_at = datetime.now()

        # Audit history entry — required on status change OR whenever decision text is recorded/amended.
        # A board decision must never be silently overwritten without an audit trail.
        is_status_changed = data.status is not None and data.status != prev_status
        is_decision_recorded = data.decision is not None
        if is_status_changed or is_decision_recorded:
            history_entry = BoardActionHistory(
                board_action_id=ba.id,
                previous_status=prev_status,
                new_status=ba.status,
                decision_notes=data.decision_notes or data.decision,
                action_notes="Decision amended via PATCH" if is_decision_recorded and not is_status_changed else None,
                changed_by_id=current_user_id,
                changed_at=datetime.now(UTC),
            )
            db.add(history_entry)

        await db.commit()
        await db.refresh(ba)
        return ba

    @staticmethod
    async def record_board_decision(
        db: AsyncSession,
        action_id: uuid.UUID,
        data: BoardActionDecisionRequest,
        current_user_id: uuid.UUID,
    ) -> BoardAction:
        stmt = (
            select(BoardAction)
            .where(
                BoardAction.id == action_id,
                BoardAction.deleted_at.is_(None)
            )
            .options(selectinload(BoardAction.history))
        )
        res = await db.execute(stmt)
        ba = res.scalar_one_or_none()
        if not ba:
            raise ValueError("Board action not found")

        prev_status = ba.status
        ba.status = data.status
        ba.decision = data.decision
        ba.decision_date = datetime.now()
        ba.decided_by_id = current_user_id
        ba.updated_by = current_user_id
        ba.updated_at = datetime.now()

        # Append-only history record ensuring no decision history is silently overwritten
        history_entry = BoardActionHistory(
            board_action_id=ba.id,
            previous_status=prev_status,
            new_status=data.status,
            decision_notes=data.decision_notes or data.decision,
            action_notes=f"Decision recorded: {data.decision}",
            changed_by_id=current_user_id,
            changed_at=datetime.now(UTC),
        )
        db.add(history_entry)
        await db.commit()
        await db.refresh(ba)
        return ba

    # ── Department Updates CRUD ───────────────────────────────────────────────

    @staticmethod
    async def submit_department_update(
        db: AsyncSession,
        data: DepartmentExecutiveUpdateCreate,
        current_user_id: uuid.UUID,
    ) -> DepartmentExecutiveUpdate:
        # Check if an update for this period + department already exists
        stmt = select(DepartmentExecutiveUpdate).where(
            DepartmentExecutiveUpdate.reporting_period == data.reporting_period,
            DepartmentExecutiveUpdate.department == data.department,
            DepartmentExecutiveUpdate.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            # Snapshot the current narrative to history before overwriting (append-only audit trail)
            snapshot = DepartmentExecutiveUpdateHistory(
                update_id=existing.id,
                reporting_period=existing.reporting_period,
                department=existing.department,
                previous_headline_summary=existing.headline_summary,
                previous_accomplishments_narrative=existing.accomplishments_narrative,
                previous_risks_issues=existing.risks_issues,
                previous_status=existing.status,
                changed_by_id=current_user_id,
                changed_at=datetime.now(UTC),
            )
            db.add(snapshot)
            # Update existing record for the period rather than violating unique constraint
            existing.headline_summary = data.headline_summary
            existing.accomplishments_narrative = data.accomplishments_narrative
            existing.risks_issues = data.risks_issues
            existing.support_decision_requested = data.support_decision_requested
            existing.status = data.status
            existing.linked_initiative_id = data.linked_initiative_id
            existing.linked_board_action_id = data.linked_board_action_id
            existing.updated_by = current_user_id
            existing.updated_at = datetime.now()
            await db.commit()
            await db.refresh(existing)
            return existing

        update = DepartmentExecutiveUpdate(
            reporting_period=data.reporting_period,
            department=data.department,
            headline_summary=data.headline_summary,
            accomplishments_narrative=data.accomplishments_narrative,
            risks_issues=data.risks_issues,
            support_decision_requested=data.support_decision_requested,
            status=data.status,
            linked_initiative_id=data.linked_initiative_id,
            linked_board_action_id=data.linked_board_action_id,
            submitted_by_id=current_user_id,
            submitted_date=datetime.now(),
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        db.add(update)
        await db.commit()
        await db.refresh(update)
        return update
