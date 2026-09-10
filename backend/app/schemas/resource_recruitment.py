"""Pydantic schemas for Resource Unit Recruitment and Dashboard.

These schemas provide request validation and response serialization for
FastAPI endpoints in the Resource Unit domain.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RecruitmentState(str, enum.Enum):
    """Authoritative recruitment pipeline stages."""

    INQUIRY = "INQUIRY"
    ORIENTATION = "ORIENTATION"
    APPLICATION = "APPLICATION"
    ASSESSMENT = "ASSESSMENT"
    APPROVAL_REVIEW = "APPROVAL_REVIEW"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
    ON_HOLD = "ON_HOLD"


class ApplicantRole(str, enum.Enum):
    """Applicant role in a recruitment application."""

    PRIMARY_APPLICANT = "PRIMARY_APPLICANT"
    SECONDARY_APPLICANT = "SECONDARY_APPLICANT"


# ── Applicant Schemas ──────────────────────────────────────────────
class RecruitmentApplicantBase(BaseModel):
    person_id: uuid.UUID = Field(..., description="UUID of the canonical Person record")
    role: ApplicantRole = Field(
        default=ApplicantRole.PRIMARY_APPLICANT, description="Applicant role"
    )
    snapshot: dict[str, Any] | None = Field(
        default=None, description="Immutable snapshot of applicant details at time of application"
    )


class RecruitmentApplicantCreate(RecruitmentApplicantBase):
    pass


class RecruitmentApplicantRead(RecruitmentApplicantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recruitment_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    person_name: str | None = None


# ── History Schemas ────────────────────────────────────────────────
class RecruitmentHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recruitment_id: uuid.UUID
    from_state: RecruitmentState
    to_state: RecruitmentState
    changed_at: datetime
    changed_by_id: uuid.UUID | None = None
    changed_by_name: str | None = None
    notes: str | None = None


# ── Recruitment Core Schemas ───────────────────────────────────────
class RecruitmentBase(BaseModel):
    resource_home_id: uuid.UUID | None = Field(
        default=None, description="Optional PlacementHome ID to allocate upon approval"
    )
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class RecruitmentCreate(RecruitmentBase):
    applicants: list[RecruitmentApplicantCreate] = Field(
        ..., min_length=1, description="Primary applicant and optional co-applicant"
    )
    initial_state: RecruitmentState = Field(
        default=RecruitmentState.INQUIRY, description="Initial recruitment stage"
    )


class RecruitmentUpdate(BaseModel):
    resource_home_id: uuid.UUID | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class RecruitmentStateTransition(BaseModel):
    to_state: RecruitmentState = Field(..., description="Target state for transition")
    notes: str | None = Field(default=None, description="Notes documenting the transition rationale")
    resource_home_id: uuid.UUID | None = Field(
        default=None, description="Optional PlacementHome to link when transitioning to APPROVED"
    )


class RecruitmentRead(RecruitmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_state: RecruitmentState
    previous_state: RecruitmentState | None = None
    created_at: datetime
    updated_at: datetime
    applicants: list[RecruitmentApplicantRead] = []
    history: list[RecruitmentHistoryRead] = []
    resource_home_code: str | None = None
    resource_home_name: str | None = None


class RecruitmentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_state: RecruitmentState
    previous_state: RecruitmentState | None = None
    resource_home_id: uuid.UUID | None = None
    resource_home_code: str | None = None
    resource_home_name: str | None = None
    primary_applicant_name: str | None = None
    applicant_count: int = 1
    created_at: datetime
    updated_at: datetime
    notes: str | None = None


# ── Resource Dashboard Metrics Schema ──────────────────────────────
class ResourceDashboardMetrics(BaseModel):
    """Authoritative metrics aggregated via database queries."""

    active_resource_homes: int = Field(
        ..., description="Count of PlacementHomes with status == 'ACTIVE'"
    )
    available_beds: int = Field(
        ..., description="Sum of (total_capacity - active_placements) across active homes"
    )
    total_capacity: int = Field(..., description="Total bed capacity across active homes")
    active_placements: int = Field(..., description="Currently active placement episodes")
    applications_by_stage: dict[str, int] = Field(
        ..., description="Count of recruitment applications in each stage"
    )
    applications_awaiting_review: int = Field(
        ..., description="Recruitments in APPLICATION, ASSESSMENT, or APPROVAL_REVIEW"
    )
    upcoming_home_renewals: int = Field(
        ..., description="Active home licenses expiring within the next 90 days"
    )
    total_applications: int = Field(..., description="Total recruitment applications in system")

    # Sprint 2 Compliance Metrics
    clearances_expiring_30_days: int = Field(
        default=0, description="Clearances/screenings expiring within 30 days"
    )
    clearances_expired: int = Field(
        default=0, description="Clearances/screenings past their expiry date"
    )
    training_due_30_days: int = Field(
        default=0, description="Caregiver training due or expiring within 30 days"
    )
    training_expired: int = Field(
        default=0, description="Caregiver training certificates currently expired"
    )
    licenses_nearing_renewal_90_days: int = Field(
        default=0, description="Placement home licenses expiring within 90 days"
    )
    inspections_overdue: int = Field(
        default=0, description="Scheduled inspections past their target date without completion"
    )
    outstanding_corrective_actions: int = Field(
        default=0, description="Visits/inspections with active/pending corrective action requirements"
    )
    non_compliant_homes_count: int = Field(
        default=0, description="Active placement homes with non-compliant clearances, licenses, or inspections"
    )

    # Sprint 3 Operational & Strategic Telemetry
    monitoring_due_30_days: int = Field(default=0, description="Ongoing monitoring reviews due in next 30 days")
    monitoring_overdue: int = Field(default=0, description="Active homes with overdue periodic monitoring")
    open_complaints_count: int = Field(default=0, description="Complaints currently open or under review")
    active_investigations_count: int = Field(default=0, description="Complaints currently under active investigation")
    caregiver_supports_active: int = Field(default=0, description="Caregiver supports requested or in progress")
    placement_stability_pct: float = Field(default=0.0, description="Percentage of placements completed without disruption")
    retention_rate_pct: float = Field(default=0.0, description="Percentage of active homes open > 1 year")
    recruitment_conversion_rate_pct: float = Field(default=0.0, description="Percentage of applicants approved")
    finance_summary: dict | None = Field(
        default=None, description="Financial roll-up visible ONLY to users with finance permissions"
    )
