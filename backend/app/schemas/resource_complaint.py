"""Pydantic schemas for Resource Home Complaints and Investigations (Sprint 3)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResourceComplaintCreate(BaseModel):
    """Schema for registering a new complaint against a Resource Home."""

    placement_home_id: uuid.UUID
    complainant_category: str = Field(
        default="ANONYMOUS",
        description="COMMUNITY_MEMBER, FOSTER_CHILD, BIRTH_PARENT, CAREGIVER, COLLATERAL, AGENCY_STAFF, ANONYMOUS",
    )
    complainant_name: str | None = None
    complainant_contact: str | None = None
    received_date: date = Field(default_factory=date.today)
    complaint_type: str = Field(
        default="CARE_STANDARDS",
        description="CARE_STANDARDS, PHYSICAL_ENVIRONMENT, SAFETY_CONCERN, BEHAVIOUR_MANAGEMENT, COMMUNICATION, POLICY_VIOLATION, OTHER",
    )
    allegation_summary: str = Field(..., min_length=5)
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    assigned_investigator_id: uuid.UUID | None = None
    incident_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None


class ResourceComplaintInvestigationUpdate(BaseModel):
    """Schema for recording investigation progress and findings."""

    investigation_activity: dict[str, Any] | None = None
    findings: str | None = None
    finalize_findings: bool = False
    recommendations: str | None = None
    corrective_actions: str | None = None
    status: str | None = None


class ResourceComplaintDisposition(BaseModel):
    """Schema for concluding and closing a complaint."""

    disposition: str = Field(
        ...,
        description="SUBSTANTIATED, UNSUBSTANTIATED, INCONCLUSIVE, RESOLVED_INFORMALLY, POLICY_ACTION_REQUIRED",
    )
    disposition_notes: str | None = None
    closure_date: date = Field(default_factory=date.today)
    status: str = "CLOSED"


class ResourceComplaintBasicResponse(BaseModel):
    """Redacted complaint record safe for general resource viewers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    placement_home_id: uuid.UUID
    complainant_category: str
    received_date: date
    complaint_type: str
    severity: str
    status: str
    closure_date: date | None = None
    disposition: str | None = None
    created_at: datetime
    home_name: str | None = None
    home_code: str | None = None


class ResourceComplaintSensitiveResponse(BaseModel):
    """Full complaint record containing sensitive complainant info, findings, and notes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    placement_home_id: uuid.UUID
    complainant_category: str
    complainant_name: str | None = None
    complainant_contact: str | None = None
    received_date: date
    complaint_type: str
    allegation_summary: str
    severity: str
    assigned_investigator_id: uuid.UUID | None = None
    status: str
    investigation_activities: list[dict[str, Any]] = Field(default_factory=list)
    findings: str | None = None
    findings_finalized: bool
    findings_finalized_at: datetime | None = None
    findings_finalized_by: uuid.UUID | None = None
    recommendations: str | None = None
    corrective_actions: str | None = None
    disposition: str | None = None
    disposition_notes: str | None = None
    disposition_by_id: uuid.UUID | None = None
    disposition_at: datetime | None = None
    closure_date: date | None = None
    incident_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    home_name: str | None = None
    home_code: str | None = None
    investigator_name: str | None = None
