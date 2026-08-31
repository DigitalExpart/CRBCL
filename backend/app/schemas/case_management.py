"""Pydantic schemas for Phase 4 Core Case Management and Case Notes."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Case Base & Extended Schemas ─────────────────────────────
class CaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    case_type: str | None = None
    priority: str | None = "Medium"
    risk_level: str | None = "Medium"
    stage: str | None = "INVESTIGATION"
    description: str | None = None
    referral_source: str | None = None
    intake_date: date | None = None
    target_resolution_date: date | None = None
    service_plan: str | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_worker_name: str | None = None
    assigned_team_id: uuid.UUID | None = None
    origin_referral_id: uuid.UUID | None = None
    origin_disposition_id: uuid.UUID | None = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: str | None = None
    status: str | None = None  # Handled with 400 rejection in service to enforce lifecycle methods
    case_type: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    stage: str | None = None
    description: str | None = None
    referral_source: str | None = None
    target_resolution_date: date | None = None
    service_plan: str | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_worker_name: str | None = None
    assigned_team_id: uuid.UUID | None = None


class CaseCloseRequest(BaseModel):
    closed_reason: str = Field(..., min_length=5, description="Mandatory detailed reason for closing the case.")
    closed_date: date | None = None


class CaseReopenRequest(BaseModel):
    reopened_reason: str = Field(..., min_length=5, description="Mandatory justification for reopening the file.")


class CaseResponse(BaseModel):
    id: uuid.UUID
    case_number: str
    title: str
    case_type: str | None = None
    status: str
    stage: str
    priority: str | None = None
    risk_level: str | None = None
    description: str | None = None
    referral_source: str | None = None
    intake_date: date | None = None
    target_resolution_date: date | None = None
    closed_date: date | None = None
    closed_reason: str | None = None
    reopened_at: datetime | None = None
    reopened_by: uuid.UUID | None = None
    reopened_reason: str | None = None
    service_plan: str | None = None
    notes: str | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    assigned_worker_id: uuid.UUID | None = None
    assigned_worker_name: str | None = None
    assigned_team_id: uuid.UUID | None = None
    origin_referral_id: uuid.UUID | None = None
    origin_disposition_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


CaseListResponse = CaseResponse


class CaseSnapshotResponse(BaseModel):
    case_id: str | uuid.UUID
    case_number: str
    title: str
    case_type: str | None = None
    status: str
    stage: str
    priority: str | None = None
    risk_level: str | None = None
    description: str | None = None
    intake_date: str | date | None = None
    closed_date: str | date | None = None
    days_open: int = 0
    primary_client: dict | None = None
    family: dict | None = None
    origin_referral: dict | None = None
    active_workers: list[dict] = []
    total_people_count: int = 0
    last_note_date: str | None = None
    next_appointment: str | None = None
    alerts: list[dict] = []


# ── Case People Schemas ───────────────────────────────────────
class CasePersonCreate(BaseModel):
    person_id: uuid.UUID
    role: str = "other"  # subject_child, sibling, parent, guardian, caregiver, person_of_concern, other
    relationship_to_subject: str | None = None
    is_primary: bool = False
    notes: str | None = None


class CasePersonResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    relationship_to_subject: str | None = None
    is_primary: bool = False
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    person_first_name: str | None = None
    person_last_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Case Assignment Schemas ───────────────────────────────────
class CaseAssignmentCreate(BaseModel):
    user_id: uuid.UUID
    role: str = "caseworker"  # primary_investigator, secondary_investigator, backup_investigator, caseworker, supervisor
    notes: str | None = None


class CaseAssignmentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    user_email: str | None = None
    role: str
    is_active: bool
    assigned_at: datetime
    unassigned_at: datetime | None = None
    notes: str | None = None

    class Config:
        from_attributes = True


# ── Case External Worker Schemas ──────────────────────────────
class CaseExternalWorkerCreate(BaseModel):
    name: str = Field(..., max_length=255)
    organization: str | None = None
    role: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CaseExternalWorkerResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    name: str
    organization: str | None = None
    role: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# ── Case Sources Schemas ──────────────────────────────────────
class CaseSourceCreate(BaseModel):
    category: str = "OTHER_SOURCE"  # OTHER_SOURCE, COLLATERAL_SOURCE
    name: str = Field(..., max_length=255)
    relationship_or_role: str | None = None
    organization: str | None = None
    person_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class CaseSourceResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    category: str
    name: str
    relationship_or_role: str | None = None
    organization: str | None = None
    person_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Case Link Schemas ─────────────────────────────────────────
class CaseLinkCreate(BaseModel):
    target_case_id: uuid.UUID
    link_type: str = "related_family"
    reason: str | None = None


class CaseLinkResponse(BaseModel):
    id: uuid.UUID
    source_case_id: uuid.UUID
    target_case_id: uuid.UUID
    target_case_number: str | None = None
    target_case_title: str | None = None
    link_type: str
    reason: str | None = None
    linked_at: datetime

    class Config:
        from_attributes = True


# ── Case Restriction Schemas ──────────────────────────────────
class CaseRestrictionCreate(BaseModel):
    user_id: uuid.UUID
    restriction_type: str = "conflict_of_interest"
    reason: str = Field(..., min_length=3)
    expires_at: datetime | None = None


class CaseRestrictionRemoval(BaseModel):
    removal_reason: str = Field(..., min_length=3)


class CaseRestrictionResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    restriction_type: str
    reason: str
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None
    removed_at: datetime | None = None
    removal_reason: str | None = None

    class Config:
        from_attributes = True


# ── Case Transfer Schemas ─────────────────────────────────────
class CaseTransferCreate(BaseModel):
    destination_team_id: uuid.UUID
    reason: str = Field(..., min_length=5)
    child_id: uuid.UUID | None = None
    submit_immediately: bool = False


class CaseTransferReview(BaseModel):
    review_notes: str | None = None


class CaseTransferResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str | None = None
    child_id: uuid.UUID | None = None
    child_name: str | None = None
    source_team_id: uuid.UUID
    source_team_name: str | None = None
    destination_team_id: uuid.UUID
    destination_team_name: str | None = None
    reason: str
    status: str
    requested_by: uuid.UUID | None = None
    requester_name: str | None = None
    requested_at: datetime
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Case Status History Schema ────────────────────────────────
class CaseStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    previous_status: str | None = None
    new_status: str
    reason: str | None = None
    changed_by: uuid.UUID | None = None
    changer_name: str | None = None
    changed_at: datetime
    notes: str | None = None

    class Config:
        from_attributes = True


# ── Case Notes Schemas ────────────────────────────────────────
class CaseNotePersonBrief(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    person_name: str | None = None
    role: str | None = None

    class Config:
        from_attributes = True


class CaseNoteAttachmentBrief(BaseModel):
    id: uuid.UUID
    file_name: str
    file_size: int | None = None
    content_type: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CaseNoteAddendumResponse(BaseModel):
    id: uuid.UUID
    case_note_id: uuid.UUID
    content: str
    reason: str
    created_by: uuid.UUID | None = None
    author_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CaseNoteAddendumCreate(BaseModel):
    content: str = Field(..., min_length=3, description="Correction or clarification content.")
    reason: str = Field(..., min_length=3, description="Justification for addendum.")


class CaseNoteCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    note_type: str = "Progress Note"
    duration_minutes: int | None = None
    contact_type: str | None = "FACE_TO_FACE"
    location: str | None = "OFFICE"
    is_well_child_checkup: bool = False
    appointment_status: str | None = None
    next_appointment_at: datetime | None = None
    goal_id: uuid.UUID | None = None
    notify_team: bool = False
    status: str = "COMPLETED"  # DRAFT, COMPLETED
    is_confidential: bool = False
    people_ids: list[uuid.UUID] = []


class CaseNoteUpdate(BaseModel):
    subject: str | None = None
    content: str | None = None
    note_type: str | None = None
    duration_minutes: int | None = None
    contact_type: str | None = None
    location: str | None = None
    is_well_child_checkup: bool | None = None
    appointment_status: str | None = None
    next_appointment_at: datetime | None = None
    goal_id: uuid.UUID | None = None
    notify_team: bool | None = None
    status: str | None = None
    is_confidential: bool | None = None
    people_ids: list[uuid.UUID] | None = None


class CaseNoteResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    subject: str
    content: str
    note_type: str
    duration_minutes: int | None = None
    contact_type: str | None = None
    location: str | None = None
    is_well_child_checkup: bool = False
    appointment_status: str | None = None
    next_appointment_at: datetime | None = None
    goal_id: uuid.UUID | None = None
    notify_team: bool = False
    status: str
    is_confidential: bool = False
    is_locked: bool = False
    locked_at: datetime | None = None
    locked_by: uuid.UUID | None = None
    author_name: str | None = None
    created_at: datetime
    updated_at: datetime
    people: list[CaseNotePersonBrief] = []
    attachments: list[CaseNoteAttachmentBrief] = []
    addenda: list[CaseNoteAddendumResponse] = []

    class Config:
        from_attributes = True


class CaseMetricsResponse(BaseModel):
    total_notes: int = 0
    total_duration_minutes: int = 0
    well_child_checkups: int = 0
    attendance: dict[str, int] = {}
    contact_types: dict[str, int] = {}
