"""Pydantic Schemas for Reporting, QA, Passports & Dashboards (Phase 11)."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Reporting Schemas ──────────────────────────────────────────
class AdHocReportRequest(BaseModel):
    dataset_key: str
    fields: list[str] | None = None
    filters: list[dict[str, Any]] | None = None
    group_by: str | None = None
    limit: int = Field(default=100, ge=1, le=5000)
    offset: int = Field(default=0, ge=0)


class SavedReportCreate(BaseModel):
    name: str
    description: str | None = None
    dataset_key: str
    team_id: uuid.UUID | None = None
    visibility: str = "PRIVATE"  # PRIVATE, TEAM, AUTHORIZED_SHARED
    configuration: dict[str, Any] = {}


class SavedReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    dataset_key: str
    owner_user_id: uuid.UUID
    team_id: uuid.UUID | None = None
    visibility: str
    configuration: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ReportExportRequest(BaseModel):
    dataset_key: str
    export_format: str = "XLSX"  # XLSX, CSV
    fields: list[str] | None = None
    filters: list[dict[str, Any]] | None = None


# ── QA Audit Schemas ───────────────────────────────────────────
class QAAuditResultInput(BaseModel):
    item_id: uuid.UUID
    compliance: str = "YES"  # YES, NO, NA
    notes: str | None = None
    finding_severity: str | None = None
    followup_required: bool = False


class QAAuditCreate(BaseModel):
    case_id: uuid.UUID
    template_version_id: uuid.UUID
    review_date: date = Field(default_factory=date.today)
    status: str = "DRAFT"  # DRAFT, IN_PROGRESS, COMPLETED
    notes: str | None = None
    results: list[QAAuditResultInput] = []


class QAAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    template_version_id: uuid.UUID
    reviewer_id: uuid.UUID
    review_date: date
    status: str
    overall_score: float | None = None
    notes: str | None = None
    completed_at: datetime | None = None
    created_at: datetime


class QATemplateItemCreate(BaseModel):
    section: str = "General Documentation"
    item_text: str
    guidance_notes: str | None = None
    severity: str = "MEDIUM"
    sort_order: int = 0
    is_required: bool = True


class QATemplateCreate(BaseModel):
    code: str
    title: str
    description: str | None = None
    cadence: str = "QUARTERLY"
    target_case_type: str | None = None
    items: list[QATemplateItemCreate] = []


# ── Dashboard Schemas ──────────────────────────────────────────
class WidgetLayoutInput(BaseModel):
    widget_key: str
    position: int = 0
    width: int = 1
    height: int = 1
    is_visible: bool = True
    settings: dict[str, Any] = {}
