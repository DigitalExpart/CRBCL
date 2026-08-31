"""Pydantic schemas for Referral, Intake, Screening, Child Dispositions, and Decisions."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Referral Person Schemas ───────────────────────────────────

class ReferralPersonCreate(BaseModel):
    person_id: uuid.UUID
    role: str  # child, parent, guardian, alleged_person_of_concern, relative, other_adult, collateral
    relationship_to_child: str | None = None
    is_primary_caregiver: bool = False
    is_subject_of_concern: bool = False
    notes: str | None = None


class ReferralPersonResponse(BaseModel):
    id: uuid.UUID
    referral_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    relationship_to_child: str | None = None
    is_primary_caregiver: bool = False
    is_subject_of_concern: bool = False
    notes: str | None = None
    created_at: datetime

    # Nested person basic summary
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    indigenous_identity: str | None = None
    band_nation: str | None = None
    phone: str | None = None

    model_config = {"from_attributes": True}


# ── Referral Reporter Schemas ─────────────────────────────────

class ReferralReporterCreate(BaseModel):
    is_anonymous: bool = False
    is_mandated_reporter: bool = False
    wants_notification: bool = False
    reporter_name: str | None = None
    organization: str | None = None
    phone: str | None = None
    email: str | None = None
    preferred_contact_method: str | None = None
    relationship_to_family: str | None = None
    reporter_notes: str | None = None


class ReferralReporterResponse(BaseModel):
    id: uuid.UUID
    referral_id: uuid.UUID
    is_anonymous: bool
    is_mandated_reporter: bool
    wants_notification: bool
    reporter_name: str | None = None
    organization: str | None = None
    phone: str | None = None
    email: str | None = None
    preferred_contact_method: str | None = None
    relationship_to_family: str | None = None
    reporter_notes: str | None = None
    is_redacted: bool = False

    model_config = {"from_attributes": True}


# ── Referral Incident Schemas ─────────────────────────────────

class ReferralIncidentCreate(BaseModel):
    incident_date: date | None = None
    incident_time: datetime | None = None
    location_description: str | None = None
    community: str | None = None
    description: str
    law_enforcement_involved: bool = False
    police_file_number: str | None = None
    officer_info: str | None = None
    immediate_danger: bool = False


class ReferralIncidentResponse(BaseModel):
    id: uuid.UUID
    referral_id: uuid.UUID
    incident_date: date | None = None
    incident_time: datetime | None = None
    location_description: str | None = None
    community: str | None = None
    description: str
    law_enforcement_involved: bool = False
    police_file_number: str | None = None
    officer_info: str | None = None
    immediate_danger: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Referral Concern Schemas ──────────────────────────────────

class ReferralConcernCreate(BaseModel):
    concern_type: str
    is_primary: bool = False
    severity: str = "Moderate"
    description: str | None = None


class ReferralConcernResponse(BaseModel):
    id: uuid.UUID
    referral_id: uuid.UUID
    concern_type: str
    is_primary: bool = False
    severity: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Child Disposition Schemas ─────────────────────────────────

class ChildDispositionCreate(BaseModel):
    person_id: uuid.UUID
    decision: str  # PROTECTION, PREVENTION, SCREEN_OUT, EXTERNAL_REFERRAL, POST_MAJORITY
    reason: str = ""
    destination_team_id: uuid.UUID | None = None
    destination_program: str | None = None
    external_agency_name: str | None = None
    external_referral_contact: str | None = None


class ChildDispositionResponse(BaseModel):
    id: uuid.UUID
    referral_id: uuid.UUID
    person_id: uuid.UUID
    decision: str
    reason: str = ""
    destination_team_id: uuid.UUID | None = None
    destination_program: str | None = None
    external_agency_name: str | None = None
    external_referral_contact: str | None = None
    resulting_case_id: uuid.UUID | None = None
    decided_by: uuid.UUID | None = None
    decided_at: datetime | None = None
    approval_state: str = "DRAFT"

    # Child details
    child_first_name: str | None = None
    child_last_name: str | None = None
    child_date_of_birth: date | None = None

    model_config = {"from_attributes": True}


# ── Intake Decision & Workflow Action Schemas ─────────────────

class IntakeDecisionSave(BaseModel):
    overall_recommendation: str = ""
    rationale: str = ""
    dispositions: list[ChildDispositionCreate] = []


class IntakeDecisionSubmit(BaseModel):
    overall_recommendation: str
    rationale: str
    dispositions: list[ChildDispositionCreate]


class IntakeDecisionApprove(BaseModel):
    supervisor_notes: str | None = None
    idempotency_key: str | None = None


class IntakeDecisionReturn(BaseModel):
    return_reason: str


class IntakeDecisionResponse(BaseModel):
    id: uuid.UUID
    referral_id: uuid.UUID
    overall_recommendation: str
    rationale: str
    supervisor_notes: str | None = None
    submitted_by: uuid.UUID | None = None
    submitted_at: datetime | None = None
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    returned_by: uuid.UUID | None = None
    returned_at: datetime | None = None
    return_reason: str | None = None

    model_config = {"from_attributes": True}


# ── Referral Link Schemas ─────────────────────────────────────

class ReferralLinkCreate(BaseModel):
    target_referral_id: uuid.UUID
    link_type: str = "related_incident"
    reason: str | None = None


class ReferralLinkResponse(BaseModel):
    id: uuid.UUID
    source_referral_id: uuid.UUID
    target_referral_id: uuid.UUID
    target_referral_number: str | None = None
    target_referral_status: str | None = None
    link_type: str
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Core Referral Schemas ─────────────────────────────────────

class ReferralCreate(BaseModel):
    received_date: date = Field(default_factory=date.today)
    received_time: datetime | None = None
    received_method: str = "phone"
    community: str | None = None
    priority: str = "Medium"
    risk_level: str | None = None
    summary: str = ""
    immediate_safety_concerns: bool = False
    law_enforcement_involved: bool = False
    law_enforcement_file_number: str | None = None
    law_enforcement_officer_info: str | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_team_id: uuid.UUID | None = None
    origin_agency: str | None = None
    notes: str | None = None

    # Embedded optional sub-entities for draft creation
    reporter: ReferralReporterCreate | None = None
    people: list[ReferralPersonCreate] = []
    concerns: list[ReferralConcernCreate] = []
    incidents: list[ReferralIncidentCreate] = []


class ReferralUpdate(BaseModel):
    received_date: date | None = None
    received_time: datetime | None = None
    received_method: str | None = None
    community: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    summary: str | None = None
    immediate_safety_concerns: bool | None = None
    law_enforcement_involved: bool | None = None
    law_enforcement_file_number: str | None = None
    law_enforcement_officer_info: str | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_team_id: uuid.UUID | None = None
    origin_agency: str | None = None
    notes: str | None = None


class ReferralResponse(BaseModel):
    id: uuid.UUID
    referral_number: str
    status: str
    received_date: date
    received_time: datetime | None = None
    received_method: str
    community: str | None = None
    priority: str
    risk_level: str | None = None
    summary: str = ""
    immediate_safety_concerns: bool = False
    law_enforcement_involved: bool = False
    law_enforcement_file_number: str | None = None
    law_enforcement_officer_info: str | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_worker_name: str | None = None
    assigned_team_id: uuid.UUID | None = None
    origin_agency: str | None = None
    notes: str | None = None
    version: int = 1
    created_at: datetime
    updated_at: datetime

    # Summary counts
    people_count: int = 0
    children_count: int = 0
    primary_concern: str | None = None

    model_config = {"from_attributes": True}


class ReferralDetailResponse(ReferralResponse):
    people: list[ReferralPersonResponse] = []
    reporter: ReferralReporterResponse | None = None
    incidents: list[ReferralIncidentResponse] = []
    concerns: list[ReferralConcernResponse] = []
    dispositions: list[ChildDispositionResponse] = []
    decision: IntakeDecisionResponse | None = None
    links: list[ReferralLinkResponse] = []

    model_config = {"from_attributes": True}


class ReferralListResponse(BaseModel):
    items: list[ReferralResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
