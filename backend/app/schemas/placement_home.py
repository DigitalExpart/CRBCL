"""Pydantic schemas for Placement Homes, Members, Licensing, Visits, Contacts, and Metrics."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Placement Home Member Schemas ───────────────────────────
class PlacementHomeMemberBase(BaseModel):
    person_id: uuid.UUID
    role: str = Field(default="PRIMARY_CAREGIVER", description="PRIMARY_CAREGIVER, SECONDARY_CAREGIVER, ADULT_HOUSEHOLD_MEMBER, YOUTH_HOUSEHOLD_MEMBER, OTHER")
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None
    is_active: bool = True
    notes: str | None = None


class PlacementHomeMemberCreate(PlacementHomeMemberBase):
    pass


class PlacementHomeMemberUpdate(BaseModel):
    role: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    notes: str | None = None


class PlacementHomeMemberRead(PlacementHomeMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_home_id: uuid.UUID
    person_name: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Placement Home License Schemas ──────────────────────────
class PlacementHomeLicenseBase(BaseModel):
    license_number: str
    license_type: str = "STANDARD_FOSTER"
    status: str = "ACTIVE"
    application_date: date | None = None
    issue_date: date | None = None
    effective_date: date = Field(default_factory=date.today)
    expiry_date: date
    renewal_date: date | None = None
    issuing_authority: str = "Ministry of Social Services / First Nation Authority"
    max_capacity: int | None = None
    conditions: str | None = None
    notes: str | None = None


class PlacementHomeLicenseCreate(PlacementHomeLicenseBase):
    pass


class PlacementHomeLicenseUpdate(BaseModel):
    license_number: str | None = None
    license_type: str | None = None
    status: str | None = None
    application_date: date | None = None
    issue_date: date | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    renewal_date: date | None = None
    issuing_authority: str | None = None
    max_capacity: int | None = None
    conditions: str | None = None
    notes: str | None = None


class PlacementHomeLicenseRenew(BaseModel):
    new_license_number: str
    effective_date: date = Field(default_factory=date.today)
    expiry_date: date
    license_type: str = "STANDARD_FOSTER"
    issuing_authority: str = "Ministry of Social Services / First Nation Authority"
    max_capacity: int | None = None
    conditions: str | None = None
    notes: str | None = None


class PlacementHomeLicenseRead(PlacementHomeLicenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_home_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── Placement Home Visit Schemas ────────────────────────────
class PlacementHomeVisitBase(BaseModel):
    visit_date: date = Field(default_factory=date.today)
    visit_type: str = "ROUTINE_INSPECTION"
    purpose: str
    summary: str
    observations: str | None = None
    follow_up_required: bool = False
    follow_up_due_date: date | None = None
    status: str = "COMPLETED"


class PlacementHomeVisitCreate(PlacementHomeVisitBase):
    pass


class PlacementHomeVisitUpdate(BaseModel):
    visit_date: date | None = None
    visit_type: str | None = None
    purpose: str | None = None
    summary: str | None = None
    observations: str | None = None
    follow_up_required: bool | None = None
    follow_up_due_date: date | None = None
    status: str | None = None


class PlacementHomeVisitRead(PlacementHomeVisitBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_home_id: uuid.UUID
    worker_id: uuid.UUID
    worker_name: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Placement Home Contact Log Schemas ──────────────────────
class PlacementHomeContactLogBase(BaseModel):
    person_id: uuid.UUID | None = None
    contact_type: str = "PHONE"
    contact_date: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: int | None = None
    subject: str
    notes: str
    follow_up_action: str | None = None


class PlacementHomeContactLogCreate(PlacementHomeContactLogBase):
    pass


class PlacementHomeContactLogUpdate(BaseModel):
    person_id: uuid.UUID | None = None
    contact_type: str | None = None
    contact_date: datetime | None = None
    duration_minutes: int | None = None
    subject: str | None = None
    notes: str | None = None
    follow_up_action: str | None = None


class PlacementHomeContactLogRead(PlacementHomeContactLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_home_id: uuid.UUID
    worker_id: uuid.UUID
    worker_name: str | None = None
    person_name: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Placement Home Main Schemas ─────────────────────────────
class PlacementHomeBase(BaseModel):
    name: str
    provider_id: uuid.UUID | None = None
    home_type: str = Field(default="LICENSED_FOSTER", description="LICENSED_FOSTER, THERAPEUTIC, KINSHIP, RELATIVE, FACILITY")
    status: str = Field(default="ACTIVE", description="ACTIVE, INACTIVE, ON_HOLD, CLOSED")
    licensing_status: str = Field(default="UNLICENSED", description="UNLICENSED, APPLICATION, PENDING, ACTIVE, SUSPENDED, EXPIRED, REVOKED, CLOSED")
    total_capacity: int = Field(default=1, ge=0)
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str = "Regina"
    province: str = "Saskatchewan"
    postal_code: str | None = None
    community: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    primary_caregiver_name: str | None = None
    intake_criteria_notes: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class PlacementHomeCreate(PlacementHomeBase):
    home_code: str | None = None


class PlacementHomeUpdate(BaseModel):
    name: str | None = None
    provider_id: uuid.UUID | None = None
    home_type: str | None = None
    status: str | None = None
    licensing_status: str | None = None
    total_capacity: int | None = Field(default=None, ge=0)
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    province: str | None = None
    postal_code: str | None = None
    community: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: str | None = None
    primary_caregiver_name: str | None = None
    intake_criteria_notes: str | None = None
    notes: str | None = None
    metadata_: dict[str, Any] | None = None


class PlacementHomeRead(PlacementHomeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    home_code: str
    occupied_beds: int = 0
    available_beds: int = 0
    provider_name: str | None = None
    is_archived: bool = False
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # Nested components
    current_license: PlacementHomeLicenseRead | None = None
    members: list[PlacementHomeMemberRead] = []
    licenses: list[PlacementHomeLicenseRead] = []
    visits: list[PlacementHomeVisitRead] = []
    contact_logs: list[PlacementHomeContactLogRead] = []


class PlacementHomeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    home_code: str
    name: str
    home_type: str
    status: str
    licensing_status: str
    total_capacity: int
    occupied_beds: int = 0
    available_beds: int = 0
    community: str | None = None
    city: str
    primary_caregiver_name: str | None = None
    is_archived: bool = False
    current_license_expiry: date | None = None
    created_at: datetime


class PlacementHomeFilter(BaseModel):
    search: str | None = None
    home_type: str | None = None
    status: str | None = None
    licensing_status: str | None = None
    community: str | None = None
    available_only: bool = False
    is_archived: bool = False
    page: int = 1
    page_size: int = 50


class PlacementHomeMetricsRead(BaseModel):
    total_homes: int = 0
    active_homes: int = 0
    licensed_homes: int = 0
    total_beds: int = 0
    occupied_beds: int = 0
    available_beds: int = 0
    homes_at_capacity: int = 0
    expiring_licenses_90d: int = 0
    expiring_licenses_30d: int = 0
    expired_licenses: int = 0
    expiring_background_checks: int = 0


class PlacementHomeMapMarkerRead(BaseModel):
    id: uuid.UUID
    home_code: str
    name: str
    home_type: str
    status: str
    licensing_status: str
    total_capacity: int
    occupied_beds: int
    available_beds: int
    community: str | None = None
    city: str
    latitude: float | None = None
    longitude: float | None = None


class PlacementHistoryItemRead(BaseModel):
    placement_id: uuid.UUID
    case_id: uuid.UUID | None = None
    case_number: str | None = None
    child_id: uuid.UUID | None = None
    child_name: str
    is_redacted: bool = False
    placement_type: str
    start_date: date
    end_date: date | None = None
    duration_days: int
    status: str
    discharge_reason: str | None = None


class HomeBackgroundCheckSummary(BaseModel):
    member_id: uuid.UUID
    member_name: str
    role: str
    check_id: uuid.UUID | None = None
    check_type: str | None = None
    status: str = "NOT_STARTED"
    clearance_number: str | None = None
    completed_date: date | None = None
    expiry_date: date | None = None
    is_expired: bool = False
    is_eligible: bool = False
