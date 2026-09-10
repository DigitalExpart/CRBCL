"""Pydantic schemas for Resource Home Monitoring (Sprint 3)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ResourceHomeMonitoringCreate(BaseModel):
    """Schema for recording an ongoing/periodic monitoring visit."""

    placement_home_id: uuid.UUID
    contact_date: date = Field(default_factory=date.today)
    contact_type: str = Field(default="IN_PERSON", description="IN_PERSON, HOME_VISIT, PHONE, VIDEO, COLLATERAL")
    child_interview_completed: bool = False
    caregiver_interview_completed: bool = False
    safety_review_completed: bool = False
    strengths: str | None = None
    concerns: str | None = None
    follow_up_required: bool = False
    follow_up_details: str | None = None
    next_review_date: date | None = None
    corrective_action_required: bool = False
    corrective_action_notes: str | None = None
    visit_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    notes: str | None = None
    status: str = Field(default="COMPLETED", description="SCHEDULED, COMPLETED, CANCELLED")
    cadence_days: int | None = Field(default=None, ge=1, le=365, description="Configurable monitoring cadence in days")


class ResourceHomeMonitoringUpdate(BaseModel):
    """Schema for updating a monitoring contact log."""

    contact_date: date | None = None
    contact_type: str | None = None
    child_interview_completed: bool | None = None
    caregiver_interview_completed: bool | None = None
    safety_review_completed: bool | None = None
    strengths: str | None = None
    concerns: str | None = None
    follow_up_required: bool | None = None
    follow_up_details: str | None = None
    next_review_date: date | None = None
    corrective_action_required: bool | None = None
    corrective_action_notes: str | None = None
    notes: str | None = None
    status: str | None = None
    cadence_days: int | None = None


class ResourceHomeMonitoringResponse(BaseModel):
    """Response schema for monitoring visit."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_home_id: uuid.UUID
    worker_id: uuid.UUID
    contact_date: date
    contact_type: str
    child_interview_completed: bool
    caregiver_interview_completed: bool
    safety_review_completed: bool
    strengths: str | None = None
    concerns: str | None = None
    follow_up_required: bool
    follow_up_details: str | None = None
    next_review_date: date | None = None
    corrective_action_required: bool
    corrective_action_notes: str | None = None
    visit_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    notes: str | None = None
    status: str
    cadence_days: int | None = None
    created_at: datetime
    updated_at: datetime
    worker_name: str | None = None
    home_name: str | None = None
    home_code: str | None = None
