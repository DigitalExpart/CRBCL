"""Pydantic schemas for CRBCL CEO Dashboard, Initiatives, Board Actions, and Department Updates."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class MeasurableMetric(BaseModel, Generic[T]):
    """Represents a metric that is either measured or explicitly flagged as unavailable."""

    value: T | None = None
    is_available: bool = True
    reason: str | None = None


# ── Strategic Initiatives Schemas ───────────────────────────────────────────


class ExecutiveInitiativeHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    initiative_id: uuid.UUID
    previous_status: str
    new_status: str
    progress_percentage: int | None = None
    update_note: str | None = None
    changed_by_name: str | None = None
    changed_at: datetime


class ExecutiveInitiativeBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str = Field(default="")
    department: str | None = Field(default=None, max_length=100)
    responsible_owner_id: uuid.UUID | None = None
    status: str = Field(default="ON_TRACK")  # ON_TRACK, AT_RISK, DELAYED, ON_HOLD, COMPLETED, CANCELLED
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    target_date: date | None = None
    start_date: date | None = None
    completion_date: date | None = None
    progress_percentage: int | None = Field(default=None, ge=0, le=100)
    latest_update: str | None = None
    reporting_notes: str | None = None


class ExecutiveInitiativeCreate(ExecutiveInitiativeBase):
    pass


class ExecutiveInitiativeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    department: str | None = None
    responsible_owner_id: uuid.UUID | None = None
    status: str | None = None
    priority: str | None = None
    target_date: date | None = None
    start_date: date | None = None
    completion_date: date | None = None
    progress_percentage: int | None = Field(default=None, ge=0, le=100)
    latest_update: str | None = None
    reporting_notes: str | None = None
    status_change_note: str | None = None


class ExecutiveInitiativeResponse(ExecutiveInitiativeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    responsible_owner_name: str | None = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime
    history: list[ExecutiveInitiativeHistoryResponse] = []


# ── Board Actions Schemas ───────────────────────────────────────────────────


class BoardActionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    board_action_id: uuid.UUID
    previous_status: str
    new_status: str
    decision_notes: str | None = None
    action_notes: str | None = None
    changed_by_name: str | None = None
    changed_at: datetime


class BoardActionBase(BaseModel):
    originating_department: str = Field(..., max_length=100)
    linked_initiative_id: uuid.UUID | None = None
    title: str = Field(..., max_length=255)
    background_summary: str
    requested_action: str
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    required_by_date: date | None = None
    is_governance_ready: bool = True


class BoardActionCreate(BoardActionBase):
    status: str = Field(default="SUBMITTED")


class BoardActionUpdate(BaseModel):
    title: str | None = None
    background_summary: str | None = None
    requested_action: str | None = None
    priority: str | None = None
    required_by_date: date | None = None
    status: str | None = None
    decision: str | None = None
    decision_notes: str | None = None
    is_governance_ready: bool | None = None


class BoardActionDecisionRequest(BaseModel):
    status: str = Field(..., description="APPROVED, DECLINED, DEFERRED, RESOLVED, WITHDRAWN")
    decision: str
    decision_notes: str | None = None


class BoardActionResponse(BoardActionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference_number: str
    status: str
    submitted_by_id: uuid.UUID | None = None
    submitted_by_name: str | None = None
    submitted_date: datetime | None = None
    decision: str | None = None
    decision_date: datetime | None = None
    decided_by_name: str | None = None
    linked_initiative_title: str | None = None
    created_at: datetime
    updated_at: datetime
    history: list[BoardActionHistoryResponse] = []


# ── Department Executive Update Schemas ──────────────────────────────────────


class DepartmentExecutiveUpdateCreate(BaseModel):
    reporting_period: str = Field(..., max_length=50, description="e.g. 2026-04 or 2026-Q1")
    department: str = Field(..., max_length=100)
    headline_summary: str = Field(..., max_length=500)
    accomplishments_narrative: str = Field(default="")
    risks_issues: str | None = None
    support_decision_requested: str | None = None
    status: str = Field(default="SUBMITTED")  # DRAFT, SUBMITTED, ACKNOWLEDGED
    linked_initiative_id: uuid.UUID | None = None
    linked_board_action_id: uuid.UUID | None = None


class DepartmentExecutiveUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporting_period: str
    department: str
    submitted_by_id: uuid.UUID | None = None
    submitted_by_name: str | None = None
    submitted_date: datetime | None = None
    headline_summary: str
    accomplishments_narrative: str
    risks_issues: str | None = None
    support_decision_requested: str | None = None
    status: str
    linked_initiative_id: uuid.UUID | None = None
    linked_initiative_title: str | None = None
    linked_board_action_id: uuid.UUID | None = None
    linked_board_action_title: str | None = None
    created_at: datetime
    updated_at: datetime


# ── High-Level CEO Dashboard Aggregate Schemas ───────────────────────────────


class CeoExecutiveSummary(BaseModel):
    """Authoritative top-level metrics for CEO command centre."""

    total_active_employees: MeasurableMetric[int]
    active_cases: MeasurableMetric[int]
    families_served: MeasurableMetric[int]
    children_in_care: MeasurableMetric[int]
    active_resource_homes: MeasurableMetric[int]
    resource_capacity: MeasurableMetric[int]
    resource_available_beds: MeasurableMetric[int]
    active_programs: MeasurableMetric[int]
    major_compliance_exceptions: MeasurableMetric[int]
    delayed_overdue_initiatives: MeasurableMetric[int]
    board_actions_awaiting_decision: MeasurableMetric[int]


class DepartmentHealthSummary(BaseModel):
    department: str
    name: str
    active_staff: int
    active_initiatives: int
    delayed_initiatives: int
    pending_board_actions: int
    has_recent_update: bool
    latest_update_period: str | None = None
    latest_update_headline: str | None = None
    operational_metric_label: str | None = None
    operational_metric_value: str | None = None


class WorkforceMetricsResponse(BaseModel):
    total_active_staff: MeasurableMetric[int]
    permanent_staff: MeasurableMetric[int]
    term_staff: MeasurableMetric[int]
    employees_on_leave: MeasurableMetric[int]
    recent_hires: MeasurableMetric[int]
    recent_resignations: MeasurableMetric[int]
    recent_terminations: MeasurableMetric[int]
    total_departures: MeasurableMetric[int]
    staff_by_department: dict[str, int]
    certification_warnings: MeasurableMetric[int]


class ServiceDeliveryResponse(BaseModel):
    protection_active_cases: MeasurableMetric[int]
    children_in_placement: MeasurableMetric[int]
    post_majority_clients: MeasurableMetric[int]
    prevention_families_supported: MeasurableMetric[int]
    active_resource_homes: MeasurableMetric[int]
    available_beds: MeasurableMetric[int]
    resource_recruitment_pipeline: MeasurableMetric[int]
    active_programs: MeasurableMetric[int]
    total_program_enrollment: MeasurableMetric[int]


class BudgetLineSummary(BaseModel):
    code: str
    name: str
    allocated_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal


class FinanceFundingResponse(BaseModel):
    total_allocated: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    active_grants_count: int
    pending_financial_approvals_count: int
    pending_approvals_total_amount: Decimal
    spending_by_program: list[BudgetLineSummary]


class ComplianceRiskItem(BaseModel):
    category: str  # INITIATIVE, RESOURCE, AUDIT, INCIDENT, BOARD
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    title: str
    department: str | None = None
    due_or_event_date: date | datetime | None = None
    details: str
    reference_id: str | None = None


class ComplianceRiskResponse(BaseModel):
    total_exceptions: int
    critical_exceptions: int
    high_exceptions: int
    items: list[ComplianceRiskItem]


class CriticalDateItem(BaseModel):
    date: date
    title: str
    category: str  # INITIATIVE, BOARD_ACTION, RESOURCE_LICENSE, QA_AUDIT, CALENDAR
    department: str | None = None
    urgency: str  # NORMAL, URGENT, OVERDUE
    reference_id: str | None = None


class CeoDashboardFullResponse(BaseModel):
    reporting_period: str
    executive_summary: CeoExecutiveSummary
    department_health: list[DepartmentHealthSummary]
    workforce: WorkforceMetricsResponse
    service_delivery: ServiceDeliveryResponse
    finance: FinanceFundingResponse
    compliance_risk: ComplianceRiskResponse
    critical_dates: list[CriticalDateItem]
    active_initiatives: list[ExecutiveInitiativeResponse]
    pending_board_actions: list[BoardActionResponse]
    recent_department_updates: list[DepartmentExecutiveUpdateResponse]
