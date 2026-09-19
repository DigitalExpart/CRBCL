"""Pydantic schemas for HR Dashboard endpoint."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel


class MetricAvailability(BaseModel):
    value: int | float | str | None = None
    is_available: bool = True
    reason: str | None = None


class RecentHireSummary(BaseModel):
    id: uuid.UUID
    employee_number: str
    first_name: str
    last_name: str
    position: str
    department: str
    hire_date: date
    photo_url: str | None = None


class ExpiringCertificationSummary(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    department: str
    cert_type: str
    identifier: str | None = None
    issued_date: date
    expiry_date: date | None = None
    status: str  # ACTIVE, EXPIRING, EXPIRED
    days_until_expiry: int | None = None


class HRDashboardSummaryResponse(BaseModel):
    # Core Workforce Counts
    total_employees: int
    active_staff_count: int
    on_leave_count: int
    terminated_count: int
    recent_hires_count: int  # Hired in last 90 days

    # Department and Position Distributions
    department_distribution: dict[str, int]
    position_distribution: dict[str, int]

    # Certifications & Compliance
    total_certifications: int
    active_certifications: int
    expiring_soon_count: int  # Expiring in next 30 days
    expired_certifications_count: int
    expiring_certifications: list[ExpiringCertificationSummary]

    # Recent Hires List
    recent_hires: list[RecentHireSummary]

    # Staffing / Caseload Linkage
    total_staffing_sessions: int
    recent_staffing_sessions_count: int

    # Defensible Unmodeled / Unavailable Metrics (Explicitly Not Fabricated)
    fte_metrics: MetricAvailability
    turnover_rate: MetricAvailability
    retention_targets: MetricAvailability
    leave_balances: MetricAvailability
    formal_onboarding_pipeline: MetricAvailability
