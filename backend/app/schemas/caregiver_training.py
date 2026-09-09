"""Pydantic schemas for Caregiver Training domain and home compliance tracking."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CaregiverTrainingBase(BaseModel):
    training_type: str = Field(
        ...,
        description="PRE_SERVICE_PRIDE, CPR_FIRST_AID, TRAUMA_INFORMED_CARE, CULTURAL_SAFETY, SUICIDE_PREVENTION, MEDICATION_ADMINISTRATION, OTHER",
    )
    course_name: str | None = None
    provider_name: str | None = None
    completion_date: date
    expiry_date: date | None = None
    document_id: uuid.UUID | None = None
    status: str = Field(default="COMPLETED", description="COMPLETED, IN_PROGRESS, EXPIRED, WAIVED")
    renewal_due_date: date | None = None
    notes: str | None = None


class CaregiverTrainingCreate(CaregiverTrainingBase):
    person_id: uuid.UUID
    placement_home_id: uuid.UUID | None = None


class CaregiverTrainingUpdate(BaseModel):
    training_type: str | None = None
    course_name: str | None = None
    provider_name: str | None = None
    completion_date: date | None = None
    expiry_date: date | None = None
    document_id: uuid.UUID | None = None
    status: str | None = None
    renewal_due_date: date | None = None
    notes: str | None = None


class CaregiverTrainingVerify(BaseModel):
    status: str = Field(default="COMPLETED", description="COMPLETED, EXPIRED, WAIVED")
    notes: str | None = None


class CaregiverTrainingResponse(CaregiverTrainingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    person_name: str | None = None
    placement_home_id: uuid.UUID | None = None
    placement_home_name: str | None = None
    verified_by: uuid.UUID | None = None
    verified_by_name: str | None = None
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CaregiverTrainingListResponse(BaseModel):
    items: list[CaregiverTrainingResponse]
    total: int


class CaregiverMemberTrainingSummary(BaseModel):
    person_id: uuid.UUID
    person_name: str
    role: str
    trainings: list[CaregiverTrainingResponse]
    mandatory_completed: list[str]
    mandatory_missing: list[str]
    is_compliant: bool


class HomeTrainingComplianceSummary(BaseModel):
    placement_home_id: uuid.UUID
    home_code: str
    home_name: str
    overall_status: str  # COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT
    total_caregivers: int
    compliant_caregivers: int
    member_summaries: list[CaregiverMemberTrainingSummary]
    expiring_soon_count: int  # within 30 days
    expired_count: int
