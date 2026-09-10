"""Pydantic schemas for Caregiver and Resource Home Supports (Sprint 3)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CaregiverSupportCreate(BaseModel):
    """Schema for requesting or logging support for a caregiver / Resource Home."""

    placement_home_id: uuid.UUID
    caregiver_person_id: uuid.UUID | None = None
    support_type: str = Field(
        default="RESPITE",
        description="FINANCIAL_SUPPORT, RESPITE, CLINICAL_SUPPORT, COUNSELLING, CULTURAL_SUPPORT, TRAINING_SUPPORT, TRANSPORTATION, OTHER",
    )
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    requested_date: date = Field(default_factory=date.today)
    provider_program_name: str | None = None
    frequency_duration: str | None = None
    service_request_id: uuid.UUID | None = None
    amount: Decimal | None = None
    document_id: uuid.UUID | None = None


class CaregiverSupportUpdate(BaseModel):
    """Schema for updating support status or delivery notes."""

    status: str | None = None
    provided_date: date | None = None
    outcome_notes: str | None = None
    frequency_duration: str | None = None
    amount: Decimal | None = None
    service_request_id: uuid.UUID | None = None
    provider_program_name: str | None = None


class CaregiverSupportResponse(BaseModel):
    """Response schema for a caregiver support record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    support_number: str
    placement_home_id: uuid.UUID
    caregiver_person_id: uuid.UUID | None = None
    support_type: str
    title: str
    description: str | None = None
    requested_date: date
    provided_date: date | None = None
    status: str
    provider_program_name: str | None = None
    worker_id: uuid.UUID
    frequency_duration: str | None = None
    outcome_notes: str | None = None
    service_request_id: uuid.UUID | None = None
    amount: Decimal | None = None
    document_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    home_name: str | None = None
    home_code: str | None = None
    caregiver_name: str | None = None
    worker_name: str | None = None
