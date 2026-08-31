"""Case schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CaseBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    case_type: str | None = None
    status: str = Field(default="Open", max_length=50)
    priority: str | None = Field(default="Normal", max_length=20)
    risk_level: str | None = Field(default="Low", max_length=20)
    description: str | None = None
    referral_source: str | None = None
    intake_date: date | None = None
    target_resolution_date: date | None = None
    closed_date: date | None = None
    service_plan: str | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_worker_name: str | None = None
    assigned_team_id: uuid.UUID | None = None


class CaseCreate(CaseBase):
    case_number: str | None = None  # Auto-generated if omitted


class CaseUpdate(BaseModel):
    title: str | None = None
    case_type: str | None = None
    status: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    description: str | None = None
    referral_source: str | None = None
    intake_date: date | None = None
    target_resolution_date: date | None = None
    closed_date: date | None = None
    service_plan: str | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_worker_name: str | None = None
    assigned_team_id: uuid.UUID | None = None


class CaseResponse(CaseBase):
    id: uuid.UUID
    case_number: str
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    version: int = 1

    model_config = {"from_attributes": True}
