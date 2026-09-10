"""Pydantic schemas for Front Desk Public Intake & Ingestion Pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GoogleFormIngestRequest(BaseModel):
    """External webhook payload coming from Google Forms via Apps Script / Integrations."""

    response_id: str | None = None  # Idempotency / external Google Form response ID
    submitter_name: str | None = None
    submitter_email: str | None = None
    submitter_phone: str | None = None
    submitter_relationship: str | None = None
    inquiry_type: str = "general_inquiry"
    urgency: str = "Medium"
    summary: str = ""
    details: str | None = None
    responses: dict[str, Any] = Field(default_factory=dict)
    source: str = "google_form"


class FrontDeskSubmissionManualCreate(BaseModel):
    """Manual intake entry recorded by Front Desk staff for walk-ins or phone calls."""

    source: str = "walk_in"  # walk_in, phone, email
    submitter_name: str | None = None
    submitter_email: str | None = None
    submitter_phone: str | None = None
    submitter_relationship: str | None = None
    inquiry_type: str = "general_inquiry"
    urgency: str = "Medium"
    summary: str
    details: str | None = None


class FrontDeskSubmissionReviewRequest(BaseModel):
    """Front Desk status transition (e.g. mark FRONT_DESK_REVIEW, DUPLICATE, OUT_OF_SCOPE, SPAM, CLOSED)."""

    status: str  # FRONT_DESK_REVIEW, DUPLICATE, OUT_OF_SCOPE, SPAM, CLOSED
    notes: str | None = None


class FrontDeskSubmissionRouteRequest(BaseModel):
    """Front Desk routes submission to receiving department."""

    destination_department: str  # from canonical DEPARTMENTS
    destination_team_id: uuid.UUID | None = None
    urgency: str = "Medium"
    routing_notes: str | None = None


class DepartmentActionRequest(BaseModel):
    """Receiving department action (DEPARTMENT_REVIEW, ACCEPTED, RETURNED_TO_FRONT_DESK, DUPLICATE, OUT_OF_SCOPE)."""

    action: str  # DEPARTMENT_REVIEW, ACCEPTED, RETURNED_TO_FRONT_DESK, DUPLICATE, OUT_OF_SCOPE
    notes: str | None = None


class CreateReferralFromSubmissionRequest(BaseModel):
    """Authorized Protection/Intake department staff creates internal Referral."""

    priority: str = "Medium"
    community: str | None = None
    immediate_safety_concerns: bool = False
    assigned_team_id: uuid.UUID | None = None
    assigned_worker_id: uuid.UUID | None = None
    notes: str | None = None


class GenericConversionRequest(BaseModel):
    """Link submission to arbitrary downstream domain record (e.g. prevention, recruitment)."""

    downstream_entity_type: str
    downstream_entity_id: uuid.UUID
    downstream_entity_reference: str | None = None
    notes: str | None = None


class DuplicateCandidateResponse(BaseModel):
    """Candidate match found in canonical Person, Client, or Family directories."""

    entity_type: str  # person, client, family
    id: uuid.UUID
    name: str
    details: str
    match_score: float
    match_reasons: list[str] = Field(default_factory=list)


class RoutingHistoryResponse(BaseModel):
    id: uuid.UUID
    previous_status: str
    new_status: str
    previous_destination: str | None = None
    new_destination: str | None = None
    changed_by_id: uuid.UUID | None = None
    changed_by_name: str | None = None
    changed_at: datetime
    reason_note: str | None = None

    model_config = {"from_attributes": True}


class ConversionLinkResponse(BaseModel):
    id: uuid.UUID
    downstream_entity_type: str
    downstream_entity_id: uuid.UUID
    downstream_entity_reference: str | None = None
    created_by_id: uuid.UUID | None = None
    created_by_name: str | None = None
    created_at: datetime
    notes: str | None = None

    model_config = {"from_attributes": True}


class FrontDeskSubmissionResponse(BaseModel):
    id: uuid.UUID
    submission_number: str
    external_response_id: str | None = None
    source: str
    status: str
    urgency: str
    destination_department: str | None = None
    destination_team_id: uuid.UUID | None = None

    submitter_name: str | None = None
    submitter_email: str | None = None
    submitter_phone: str | None = None
    submitter_relationship: str | None = None
    inquiry_type: str
    summary: str
    details: str | None = None
    payload_raw: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime

    front_desk_worker_id: uuid.UUID | None = None
    front_desk_worker_name: str | None = None
    front_desk_notes: str | None = None

    department_worker_id: uuid.UUID | None = None
    department_worker_name: str | None = None
    department_notes: str | None = None

    resulting_referral_id: uuid.UUID | None = None
    resulting_referral_number: str | None = None

    routing_history: list[RoutingHistoryResponse] = Field(default_factory=list)
    conversion_links: list[ConversionLinkResponse] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FrontDeskStatsResponse(BaseModel):
    received_count: int
    front_desk_review_count: int
    routed_count: int
    department_review_count: int
    accepted_count: int
    returned_count: int
    duplicate_count: int
    out_of_scope_count: int
    closed_count: int
    spam_count: int
    total_count: int
    oldest_unreviewed_hours: float | None = None
    department_counts: dict[str, int] = Field(default_factory=dict)
