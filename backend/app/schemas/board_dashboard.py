"""Board Dashboard governance schemas.

Strictly redacted, governance-safe response models for the CRBCL Board of Governors.
Under no circumstances are client/child identifiers, clinical narratives, reporter details,
staff HR personnel files, or transaction-level finances included here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BoardSummaryMetric(BaseModel):
    """Governance KPI metric with availability indicator."""

    value: Any = None
    is_available: bool = True
    reason: str | None = None
    unit: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BoardSummaryResponse(BaseModel):
    """High-level governance overview metrics for Board consideration."""

    initiatives_total: int = 0
    initiatives_on_track: int = 0
    initiatives_at_risk: int = 0
    initiatives_delayed: int = 0
    board_actions_pending: int = 0
    board_actions_total: int = 0
    total_workforce: BoardSummaryMetric
    active_care_placements: BoardSummaryMetric
    families_supported: BoardSummaryMetric
    approved_bed_capacity: BoardSummaryMetric
    approved_budget_total: Decimal = Decimal("0.00")
    approved_budget_spent: Decimal = Decimal("0.00")
    approved_budget_remaining: Decimal = Decimal("0.00")
    major_compliance_exceptions: int = 0

    model_config = ConfigDict(from_attributes=True)


class BoardActionHistoryItem(BaseModel):
    """Governance decision audit history entry."""

    id: uuid.UUID
    previous_status: str
    new_status: str
    decision_notes: str | None = None
    action_notes: str | None = None
    changed_by_name: str | None = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardActionItem(BaseModel):
    """Governance action item submitted for Board attention or resolution."""

    id: uuid.UUID
    reference_number: str
    originating_department: str
    title: str
    background_summary: str
    requested_action: str
    priority: str
    required_by_date: date | None = None
    status: str
    decision: str | None = None
    decision_date: datetime | None = None
    decided_by_name: str | None = None
    is_governance_ready: bool = True
    history: list[BoardActionHistoryItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BoardInitiativeItem(BaseModel):
    """Strategic organizational initiative approved for Board visibility."""

    id: uuid.UUID
    title: str
    department: str | None = None
    status: str
    priority: str
    target_date: date | None = None
    progress_percentage: int | None = None
    board_summary: str | None = None
    latest_update: str | None = None
    approved_for_board_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BoardDepartmentUpdateItem(BaseModel):
    """Periodic department executive update approved for Board review."""

    id: uuid.UUID
    department: str
    reporting_period: str
    headline_summary: str
    accomplishments_narrative: str
    risks_issues: str | None = None
    support_decision_requested: str | None = None
    submitted_date: datetime | None = None
    approved_for_board_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BoardWorkforceResponse(BaseModel):
    """High-level aggregate workforce metrics."""

    total_active_staff: BoardSummaryMetric
    staff_on_leave: BoardSummaryMetric
    recent_hires_in_period: BoardSummaryMetric
    staff_by_department: dict[str, int] = Field(default_factory=dict)
    fte_count: BoardSummaryMetric
    turnover_rate: BoardSummaryMetric
    contract_type_metric: BoardSummaryMetric
    exit_reason_metric: BoardSummaryMetric

    model_config = ConfigDict(from_attributes=True)


class BoardFinanceResponse(BaseModel):
    """Approved aggregate organizational finance metrics."""

    total_allocated_budget: Decimal = Decimal("0.00")
    total_expenditure: Decimal = Decimal("0.00")
    remaining_budget: Decimal = Decimal("0.00")
    active_grants_count: int = 0
    pending_purchase_orders_count: int = 0
    pending_purchase_orders_amount: Decimal = Decimal("0.00")
    budget_by_program: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BoardPerformanceResponse(BaseModel):
    """Aggregate service delivery and operational outcome indicators."""

    active_cases_total: BoardSummaryMetric
    families_served: BoardSummaryMetric
    children_in_active_placements: BoardSummaryMetric
    active_resource_homes: BoardSummaryMetric
    available_resource_beds: BoardSummaryMetric
    resource_recruitment_pipeline: BoardSummaryMetric
    active_cultural_programs: BoardSummaryMetric
    cultural_program_enrollment: BoardSummaryMetric

    model_config = ConfigDict(from_attributes=True)


class BoardRiskItem(BaseModel):
    """High-level risk and compliance exception item."""

    category: str
    title: str
    severity: str
    status: str
    due_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class BoardRiskResponse(BaseModel):
    """Organizational risk register and compliance summaries."""

    delayed_initiatives_count: int = 0
    expiring_licenses_30d_count: int = 0
    serious_incidents_total: int = 0
    serious_incidents_by_severity: dict[str, int] = Field(default_factory=dict)
    risk_items: list[BoardRiskItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BoardCriticalDateItem(BaseModel):
    """Governance deadline or milestone."""

    id: str
    title: str
    event_type: str  # BOARD_ACTION_DEADLINE, INITIATIVE_TARGET, GOVERNANCE_DEADLINE
    date: date
    urgency: str  # NORMAL, URGENT, OVERDUE
    department: str | None = None
    reference_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Request schemas for executive publishing and decision recording
class BoardPublishInitiativeRequest(BaseModel):
    is_board_visible: bool = True
    board_summary: str | None = None


class BoardPublishDepartmentUpdateRequest(BaseModel):
    is_board_visible: bool = True


class BoardRecordDecisionRequest(BaseModel):
    decision: str = Field(..., min_length=1)
    status: str = "RESOLVED"  # APPROVED, DECLINED, DEFERRED, RESOLVED
    resolution_notes: str | None = None
