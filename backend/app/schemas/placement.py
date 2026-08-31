"""Pydantic schemas for Placements, Active Efforts, Removals, Respite, Discharge, Permanency, Visitation, Court & Background Checks."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Active Efforts Schemas ───────────────────────────────────────────
class ActiveEffortCreate(BaseModel):
    effort_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    service_category: str | None = None
    provider_name: str | None = None
    service_date: date
    outcome: str = Field("ONGOING", description="SUCCESSFUL, ONGOING, UNSUCCESSFUL, REFUSED")
    barriers_encountered: str | None = None
    remedial_action: str | None = None
    worker_id: uuid.UUID | None = None


class ActiveEffortUpdate(BaseModel):
    effort_type: str | None = None
    description: str | None = None
    service_category: str | None = None
    provider_name: str | None = None
    service_date: date | None = None
    outcome: str | None = None
    barriers_encountered: str | None = None
    remedial_action: str | None = None
    worker_id: uuid.UUID | None = None


class ActiveEffortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    effort_type: str
    description: str
    service_category: str | None = None
    provider_name: str | None = None
    service_date: date
    outcome: str
    barriers_encountered: str | None = None
    remedial_action: str | None = None
    worker_id: uuid.UUID | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class ActiveEffortListResponse(BaseModel):
    items: list[ActiveEffortResponse]
    total: int


# ── Background Checks Schemas ────────────────────────────────────────
class BackgroundCheckCreate(BaseModel):
    subject_type: str = Field(..., description="CLIENT, PERSON, PLACEMENT_PROVIDER, VOLUNTEER, STAFF, OTHER")
    subject_id: uuid.UUID | None = None
    subject_name: str = Field(..., min_length=1, max_length=255)
    check_type: str = Field(..., description="CRIMINAL_RECORD, CHILD_ABUSE_REGISTRY, VULNERABLE_SECTOR, REFERENCE_CHECK")
    request_date: date
    conducted_by_agency: str | None = None
    clearance_reference_number: str | None = None
    risk_assessment_notes: str | None = None


class BackgroundCheckUpdate(BaseModel):
    subject_type: str | None = None
    subject_id: uuid.UUID | None = None
    subject_name: str | None = None
    check_type: str | None = None
    request_date: date | None = None
    completion_date: date | None = None
    expiry_date: date | None = None
    conducted_by_agency: str | None = None
    clearance_reference_number: str | None = None
    risk_assessment_notes: str | None = None


class BackgroundCheckAdjudicate(BaseModel):
    status: str = Field(..., description="PASSED, FAILED, CONDITIONAL, EXPIRED")
    is_eligible_for_placement: bool
    completion_date: date | None = None
    expiry_date: date | None = None
    risk_assessment_notes: str | None = None


class BackgroundCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID | None = None
    subject_name: str
    check_type: str
    status: str
    request_date: date
    completion_date: date | None = None
    expiry_date: date | None = None
    conducted_by_agency: str | None = None
    clearance_reference_number: str | None = None
    risk_assessment_notes: str | None = None
    is_eligible_for_placement: bool
    adjudicated_by: uuid.UUID | None = None
    adjudicated_at: datetime | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class BackgroundCheckListResponse(BaseModel):
    items: list[BackgroundCheckResponse]
    total: int


# ── In-Home Placement Schemas ────────────────────────────────────────
class InHomePlacementCreate(BaseModel):
    child_id: uuid.UUID
    primary_caregiver_id: uuid.UUID | None = None
    caregiver_relationship: str | None = None
    start_date: date
    supervision_level: str = Field("STANDARD", description="MINIMAL, STANDARD, INTENSIVE")
    safety_monitoring_frequency: str = Field("WEEKLY", description="DAILY, WEEKLY, BIWEEKLY, MONTHLY")
    support_services_provided: dict[str, Any] | list[Any] | None = None
    notes: str | None = None


class InHomePlacementUpdate(BaseModel):
    primary_caregiver_id: uuid.UUID | None = None
    caregiver_relationship: str | None = None
    supervision_level: str | None = None
    safety_monitoring_frequency: str | None = None
    support_services_provided: dict[str, Any] | list[Any] | None = None
    notes: str | None = None


class InHomePlacementEnd(BaseModel):
    end_date: date
    status: str = Field("ENDED", description="ENDED, ESCALATED_TO_REMOVAL")
    closure_reason: str | None = None
    notes: str | None = None


class InHomePlacementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    child_id: uuid.UUID
    primary_caregiver_id: uuid.UUID | None = None
    caregiver_relationship: str | None = None
    start_date: date
    end_date: date | None = None
    status: str
    supervision_level: str
    safety_monitoring_frequency: str
    support_services_provided: dict[str, Any] | list[Any] | None = None
    closure_reason: str | None = None
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class InHomePlacementListResponse(BaseModel):
    items: list[InHomePlacementResponse]
    total: int


# ── Removal Episode Schemas ──────────────────────────────────────────
class RemovalEpisodeCreate(BaseModel):
    child_id: uuid.UUID
    removal_date: date
    removal_time: time | None = None
    removal_type: str = Field(..., description="VOLUNTARY, EMERGENCY_ORDER, COURT_APPREHENSION, TEMPORARY_CUSTODY")
    authority_type: str = Field(..., description="CHILD_WELFARE_WARRANT, CONSENT_AGREEMENT, POLICE_ASSISTANCE, COURT_ORDER")
    legal_authority_reference: str | None = None
    reason_for_removal: str = Field(..., min_length=1)
    immediate_safety_threat: str | None = None
    removal_location: str | None = None
    accompanying_officers: str | None = None
    child_condition_at_removal: str | None = None
    belongings_inventoried: bool = False


class RemovalEpisodeUpdate(BaseModel):
    removal_date: date | None = None
    removal_time: time | None = None
    removal_type: str | None = None
    authority_type: str | None = None
    legal_authority_reference: str | None = None
    reason_for_removal: str | None = None
    immediate_safety_threat: str | None = None
    removal_location: str | None = None
    accompanying_officers: str | None = None
    child_condition_at_removal: str | None = None
    belongings_inventoried: bool | None = None
    status: str | None = None


class RemovalEpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    child_id: uuid.UUID
    removal_date: date
    removal_time: time | None = None
    removal_type: str
    authority_type: str
    legal_authority_reference: str | None = None
    reason_for_removal: str
    immediate_safety_threat: str | None = None
    removal_location: str | None = None
    accompanying_officers: str | None = None
    child_condition_at_removal: str | None = None
    belongings_inventoried: bool
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class RemovalEpisodeListResponse(BaseModel):
    items: list[RemovalEpisodeResponse]
    total: int


# ── Placement Episode Schemas ────────────────────────────────────────
class PlacementEpisodeCreate(BaseModel):
    child_id: uuid.UUID
    removal_episode_id: uuid.UUID | None = None
    placement_type: str = Field(..., description="KINSHIP, CUSTOMARY_CARE, FOSTER_HOME, GROUP_HOME, INDEPENDENT_LIVING, OTHER")
    provider_name: str = Field(..., min_length=1, max_length=255)
    provider_contact: str | None = None
    provider_address: str | None = None
    start_date: date
    primary_caregiver_name: str | None = None
    per_diem_rate: Decimal | None = None
    cultural_plan_in_place: bool = False
    placement_notes: str | None = None


class PlacementEpisodeUpdate(BaseModel):
    placement_type: str | None = None
    provider_name: str | None = None
    provider_contact: str | None = None
    provider_address: str | None = None
    primary_caregiver_name: str | None = None
    per_diem_rate: Decimal | None = None
    cultural_plan_in_place: bool | None = None
    placement_notes: str | None = None
    status: str | None = None


class PlacementEpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    child_id: uuid.UUID
    removal_episode_id: uuid.UUID | None = None
    placement_type: str
    provider_name: str
    provider_contact: str | None = None
    provider_address: str | None = None
    start_date: date
    end_date: date | None = None
    status: str
    primary_caregiver_name: str | None = None
    per_diem_rate: Decimal | None = None
    cultural_plan_in_place: bool
    placement_notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class PlacementEpisodeListResponse(BaseModel):
    items: list[PlacementEpisodeResponse]
    total: int


# ── Respite Episode Schemas ──────────────────────────────────────────
class RespiteEpisodeCreate(BaseModel):
    respite_provider_name: str = Field(..., min_length=1, max_length=255)
    respite_type: str = Field("PLANNED", description="PLANNED, EMERGENCY")
    start_date: date
    end_date: date
    reason: str | None = None
    status: str = Field("SCHEDULED", description="SCHEDULED, ACTIVE, COMPLETED, CANCELLED")
    notes: str | None = None


class RespiteEpisodeUpdate(BaseModel):
    respite_provider_name: str | None = None
    respite_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None
    status: str | None = None
    notes: str | None = None


class RespiteEpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_episode_id: uuid.UUID
    respite_provider_name: str
    respite_type: str
    start_date: date
    end_date: date
    reason: str | None = None
    status: str
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class RespiteEpisodeListResponse(BaseModel):
    items: list[RespiteEpisodeResponse]
    total: int


# ── Discharge Episode Schemas ────────────────────────────────────────
class DischargeEpisodeCreate(BaseModel):
    discharge_date: date
    discharge_type: str = Field(..., description="REUNIFICATION, CUSTOMARY_ADOPTION, PERMANENT_KINSHIP, AGING_OUT, TRANSFER, OTHER")
    destination_name: str | None = None
    destination_relationship: str | None = None
    post_discharge_supervision_plan: str | None = None
    discharge_readiness_assessed: bool = True
    notes: str | None = None


class DischargeEpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placement_episode_id: uuid.UUID
    discharge_date: date
    discharge_type: str
    destination_name: str | None = None
    destination_relationship: str | None = None
    post_discharge_supervision_plan: str | None = None
    discharge_readiness_assessed: bool
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


# ── Permanency Plan Schemas ──────────────────────────────────────────
class PermanencyPlanCreate(BaseModel):
    child_id: uuid.UUID
    primary_goal: str = Field(..., description="REUNIFICATION, CUSTOMARY_CARE, KINSHIP_LEGAL_CUSTODY, ADOPTION, INDEPENDENT_LIVING, OTHER")
    concurrent_goal: str | None = None
    target_date: date | None = None
    cultural_heritage_strategy: str | None = None
    sibling_co_placement_strategy: str | None = None
    review_frequency_months: int = 6
    next_review_date: date | None = None
    notes: str | None = None


class PermanencyPlanUpdate(BaseModel):
    primary_goal: str | None = None
    concurrent_goal: str | None = None
    target_date: date | None = None
    status: str | None = Field(None, description="DRAFT, ACTIVE, ACHIEVED, MODIFIED, CLOSED")
    cultural_heritage_strategy: str | None = None
    sibling_co_placement_strategy: str | None = None
    review_frequency_months: int | None = None
    next_review_date: date | None = None
    notes: str | None = None


class PermanencyPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    child_id: uuid.UUID
    primary_goal: str
    concurrent_goal: str | None = None
    target_date: date | None = None
    status: str
    cultural_heritage_strategy: str | None = None
    sibling_co_placement_strategy: str | None = None
    review_frequency_months: int
    next_review_date: date | None = None
    established_by: uuid.UUID | None = None
    approved_by: uuid.UUID | None = None
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class PermanencyPlanListResponse(BaseModel):
    items: list[PermanencyPlanResponse]
    total: int


# ── Visitation Plan Schemas ──────────────────────────────────────────
class VisitationPlanCreate(BaseModel):
    child_id: uuid.UUID
    participant_names: dict[str, Any] | list[Any] | None = None
    frequency: str = Field("WEEKLY", description="DAILY, WEEKLY, BIWEEKLY, MONTHLY, SPECIAL_OCCASIONS")
    duration_hours: Decimal | None = None
    supervision_required: bool = True
    supervisor_type: str = Field("CASE_WORKER", description="CASE_WORKER, FAMILY_SUPPORT_WORKER, UNMONITORED, THIRD_PARTY")
    location: str | None = None
    conditions: str | None = None
    effective_from: date
    effective_to: date | None = None
    notes: str | None = None


class VisitationPlanUpdate(BaseModel):
    participant_names: dict[str, Any] | list[Any] | None = None
    frequency: str | None = None
    duration_hours: Decimal | None = None
    supervision_required: bool | None = None
    supervisor_type: str | None = None
    location: str | None = None
    conditions: str | None = None
    status: str | None = Field(None, description="ACTIVE, SUSPENDED, MODIFIED, TERMINATED")
    effective_from: date | None = None
    effective_to: date | None = None
    notes: str | None = None


class VisitationPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    child_id: uuid.UUID
    participant_names: dict[str, Any] | list[Any] | None = None
    frequency: str
    duration_hours: Decimal | None = None
    supervision_required: bool
    supervisor_type: str
    location: str | None = None
    conditions: str | None = None
    status: str
    effective_from: date
    effective_to: date | None = None
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class VisitationPlanListResponse(BaseModel):
    items: list[VisitationPlanResponse]
    total: int


# ── Court Event Schemas ──────────────────────────────────────────────
class CourtEventCreate(BaseModel):
    child_id: uuid.UUID | None = None
    hearing_type: str = Field(..., description="INITIAL_APPEARANCE, PROTECTION_HEARING, TEMPORARY_CUSTODY_REVIEW, PERMANENCY_HEARING, STATUS_REVIEW, BAND_REPRESENTATION_HEARING, OTHER")
    court_docket_number: str | None = None
    court_location: str | None = None
    judge_name: str | None = None
    hearing_date: date
    hearing_time: time | None = None
    outcome_summary: str | None = None
    orders_issued: str | None = None
    legal_counsel_info: str | None = None
    band_representative_present: bool = False
    next_court_date: date | None = None
    status: str = Field("SCHEDULED", description="SCHEDULED, COMPLETED, ADJOURNED, CANCELLED")


class CourtEventUpdate(BaseModel):
    child_id: uuid.UUID | None = None
    hearing_type: str | None = None
    court_docket_number: str | None = None
    court_location: str | None = None
    judge_name: str | None = None
    hearing_date: date | None = None
    hearing_time: time | None = None
    outcome_summary: str | None = None
    orders_issued: str | None = None
    legal_counsel_info: str | None = None
    band_representative_present: bool | None = None
    next_court_date: date | None = None
    status: str | None = None


class CourtEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    child_id: uuid.UUID | None = None
    hearing_type: str
    court_docket_number: str | None = None
    court_location: str | None = None
    judge_name: str | None = None
    hearing_date: date
    hearing_time: time | None = None
    outcome_summary: str | None = None
    orders_issued: str | None = None
    legal_counsel_info: str | None = None
    band_representative_present: bool
    next_court_date: date | None = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


class CourtEventListResponse(BaseModel):
    items: list[CourtEventResponse]
    total: int


# ── Child Longitudinal Episodes Aggregate Response ────────────────────
class ChildLongitudinalEpisodesResponse(BaseModel):
    child_id: uuid.UUID
    in_home_placements: list[InHomePlacementResponse]
    removal_episodes: list[RemovalEpisodeResponse]
    placement_episodes: list[PlacementEpisodeResponse]
    permanency_plans: list[PermanencyPlanResponse]
    visitation_plans: list[VisitationPlanResponse]
    court_events: list[CourtEventResponse]
