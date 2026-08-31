"""Pydantic schemas for Safety Plans, Case Plans, Goals, Activities, Signatures."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Participant Schemas ──────────────────────────────────────────────
class PlanParticipantCreate(BaseModel):
    participant_type: str = Field(..., description="WORKER, FAMILY_MEMBER, CHILD_YOUTH, ELDER, PROVIDER, EXTERNAL_WORKER, OTHER")
    user_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=255)
    relationship: str | None = None
    role: str | None = None
    attendance_status: str = Field("ATTENDED", description="ATTENDED, EXCUSED, ABSENT, CONTRIBUTED_REMOTELY")
    signature_required: bool = True


class PlanParticipantUpdate(BaseModel):
    participant_type: str | None = None
    user_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    name: str | None = None
    relationship: str | None = None
    role: str | None = None
    attendance_status: str | None = None
    signature_required: bool | None = None


class PlanParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_version_id: uuid.UUID
    participant_type: str
    user_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    provider_id: uuid.UUID | None = None
    name: str
    relationship: str | None = None
    role: str | None = None
    attendance_status: str
    signature_required: bool
    created_at: datetime


# ── Concern / Harm Statement Schemas ─────────────────────────────────
class PlanConcernCreate(BaseModel):
    concern_type: str = Field("SAFETY_CONCERN", description="HARM_STATEMENT, DANGER_STATEMENT, SAFETY_CONCERN, WORRY")
    statement: str = Field(..., min_length=1)
    severity: str | None = Field(None, description="Low, Medium, High, Critical")
    sort_order: int = 0


class PlanConcernUpdate(BaseModel):
    concern_type: str | None = None
    statement: str | None = None
    severity: str | None = None
    sort_order: int | None = None


class PlanConcernResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_version_id: uuid.UUID
    concern_type: str
    statement: str
    severity: str | None = None
    sort_order: int
    created_at: datetime


# ── Strength / Protective Factor Schemas ─────────────────────────────
class PlanStrengthCreate(BaseModel):
    category: str | None = Field(None, description="Kinship Support, Cultural Connections, Caregiver Capacities, Community")
    statement: str = Field(..., min_length=1)
    sort_order: int = 0


class PlanStrengthUpdate(BaseModel):
    category: str | None = None
    statement: str | None = None
    sort_order: int | None = None


class PlanStrengthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_version_id: uuid.UUID
    category: str | None = None
    statement: str
    sort_order: int
    created_at: datetime


# ── Activity Schemas ─────────────────────────────────────────────────
class PlanActivityCreate(BaseModel):
    activity_text: str = Field(..., min_length=1)
    responsible_type: str = Field("WORKER", description="WORKER, FAMILY_MEMBER, PROVIDER, COMMUNITY, OTHER")
    responsible_user_id: uuid.UUID | None = None
    responsible_person_id: uuid.UUID | None = None
    responsible_name: str | None = None
    due_date: date | None = None
    status: str = Field("NOT_STARTED", description="NOT_STARTED, IN_PROGRESS, COMPLETED, CANCELLED")
    sort_order: int = 0


class PlanActivityUpdate(BaseModel):
    activity_text: str | None = None
    responsible_type: str | None = None
    responsible_user_id: uuid.UUID | None = None
    responsible_person_id: uuid.UUID | None = None
    responsible_name: str | None = None
    due_date: date | None = None
    status: str | None = None
    completion_notes: str | None = None
    sort_order: int | None = None


class PlanActivityCompleteRequest(BaseModel):
    completion_notes: str | None = None


class PlanActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    activity_text: str
    responsible_type: str
    responsible_user_id: uuid.UUID | None = None
    responsible_person_id: uuid.UUID | None = None
    responsible_name: str | None = None
    due_date: date | None = None
    status: str
    completed_at: datetime | None = None
    completion_notes: str | None = None
    sort_order: int
    created_at: datetime
    is_overdue: bool = False


# ── Goal Progress Update Schemas ─────────────────────────────────────
class GoalProgressUpdateCreate(BaseModel):
    status: str = Field(..., description="IN_PROGRESS, COMPLETED, DEFERRED, CANCELLED")
    notes: str = Field(..., min_length=1)


class GoalProgressUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    status: str
    notes: str
    updated_by: uuid.UUID | None = None
    created_at: datetime


# ── Goal Schemas ─────────────────────────────────────────────────────
class PlanGoalCreate(BaseModel):
    goal_text: str = Field(..., min_length=1)
    category: str | None = None
    target_date: date | None = None
    status: str = Field("NOT_STARTED", description="NOT_STARTED, IN_PROGRESS, COMPLETED, DEFERRED, CANCELLED")
    sort_order: int = 0
    activities: list[PlanActivityCreate] = []


class PlanGoalUpdate(BaseModel):
    goal_text: str | None = None
    category: str | None = None
    target_date: date | None = None
    status: str | None = None
    sort_order: int | None = None


class PlanGoalCompleteRequest(BaseModel):
    notes: str | None = None


class PlanGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_version_id: uuid.UUID
    goal_text: str
    category: str | None = None
    target_date: date | None = None
    status: str
    sort_order: int
    completed_at: datetime | None = None
    completed_by: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    is_overdue: bool = False
    activities: list[PlanActivityResponse] = []
    progress_updates: list[GoalProgressUpdateResponse] = []


# ── Signature Schemas ────────────────────────────────────────────────
class PlanSignatureCreate(BaseModel):
    signer_type: str = Field(..., description="WORKER, PARENT_GUARDIAN, CHILD_YOUTH, ELDER, PROVIDER, OTHER")
    signer_user_id: uuid.UUID | None = None
    signer_person_id: uuid.UUID | None = None
    signer_name: str = Field(..., min_length=1, max_length=255)
    signer_role: str = Field(..., min_length=1, max_length=100)
    signature_data: str | None = Field(None, description="Base64 canvas drawing or vector coordinates")
    signature_image_url: str | None = None
    method: str = Field("ELECTRONIC_DRAW", description="ELECTRONIC_DRAW, ELECTRONIC_TYPE, PHYSICAL_UPLOAD")
    attestation_text: str | None = None
    ip_address: str | None = None


class PhysicalSignatureUploadRequest(BaseModel):
    signer_name: str = Field(..., min_length=1, max_length=255)
    signer_role: str = Field(..., min_length=1, max_length=100)
    signer_type: str = Field("PARENT_GUARDIAN", description="WORKER, PARENT_GUARDIAN, CHILD_YOUTH, ELDER, PROVIDER, OTHER")
    document_url: str = Field(..., description="URL / ID of uploaded scanned file in Document repository")
    notes: str | None = None


class PlanSignatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_version_id: uuid.UUID
    signer_type: str
    signer_user_id: uuid.UUID | None = None
    signer_person_id: uuid.UUID | None = None
    signer_name: str
    signer_role: str
    signature_data: str | None = None
    signature_image_url: str | None = None
    signed_at: datetime
    method: str
    document_hash: str
    attestation_text: str | None = None
    ip_address: str | None = None
    created_at: datetime


# ── Plan Assessment Linkage Schemas ──────────────────────────────────
class PlanAssessmentLinkCreate(BaseModel):
    assessment_id: uuid.UUID
    relationship_type: str = Field("INFORMED_BY", description="INFORMED_BY, ORIGINATING_ASSESSMENT")
    notes: str | None = None


class PlanAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    assessment_id: uuid.UUID
    relationship_type: str
    notes: str | None = None
    created_at: datetime
    assessment_number: str | None = None
    assessment_title: str | None = None
    assessment_template_key: str | None = None


# ── Plan Version Schemas ─────────────────────────────────────────────
class PlanVersionCreate(BaseModel):
    meeting_date: datetime | None = None
    meeting_location: str | None = None
    narrative: str | None = None
    source_version_id: uuid.UUID | None = None
    participants: list[PlanParticipantCreate] = []
    concerns: list[PlanConcernCreate] = []
    strengths: list[PlanStrengthCreate] = []
    goals: list[PlanGoalCreate] = []


class PlanVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    version_number: int
    status: str
    meeting_date: datetime | None = None
    meeting_location: str | None = None
    narrative: str | None = None
    source_version_id: uuid.UUID | None = None
    document_hash: str | None = None
    finalized_at: datetime | None = None
    finalized_by: uuid.UUID | None = None
    locked_at: datetime | None = None
    locked_by: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime


class PlanVersionDetailResponse(PlanVersionResponse):
    participants: list[PlanParticipantResponse] = []
    concerns: list[PlanConcernResponse] = []
    strengths: list[PlanStrengthResponse] = []
    goals: list[PlanGoalResponse] = []
    signatures: list[PlanSignatureResponse] = []


# ── Plan Master Schemas ──────────────────────────────────────────────
class PlanCreate(BaseModel):
    case_id: uuid.UUID
    primary_person_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    plan_type: str = Field(..., description="SAFETY_PLAN, CASE_PLAN")
    title: str = Field(..., min_length=1, max_length=255)
    meeting_date: datetime | None = None
    meeting_location: str | None = None
    narrative: str | None = None
    assessment_ids: list[uuid.UUID] = []
    participants: list[PlanParticipantCreate] = []
    concerns: list[PlanConcernCreate] = []
    strengths: list[PlanStrengthCreate] = []
    goals: list[PlanGoalCreate] = []


class PlanUpdate(BaseModel):
    title: str | None = None
    primary_person_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    meeting_date: datetime | None = None
    meeting_location: str | None = None
    narrative: str | None = None


class GoalMetricsResponse(BaseModel):
    total_goals: int = 0
    not_started_goals: int = 0
    in_progress_goals: int = 0
    completed_goals: int = 0
    overdue_goals: int = 0
    total_activities: int = 0
    completed_activities: int = 0
    overdue_activities: int = 0
    completion_percentage: float = 0.0


class PlanSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    plan_type: str
    plan_number: str
    title: str
    status: str
    current_version_number: int = 1
    meeting_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
    metrics: GoalMetricsResponse = Field(default_factory=GoalMetricsResponse)
    signatures_count: int = 0
    signatures_required: int = 0


class PlanDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    primary_person_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    plan_type: str
    plan_number: str
    title: str
    status: str
    current_version_id: uuid.UUID | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    current_version: PlanVersionDetailResponse | None = None
    versions: list[PlanVersionResponse] = []
    assessments: list[PlanAssessmentResponse] = []
    metrics: GoalMetricsResponse = Field(default_factory=GoalMetricsResponse)


# ── Action Request Schemas ───────────────────────────────────────────
class PlanCloneRequest(BaseModel):
    new_title: str | None = None
    meeting_date: datetime | None = None
    meeting_location: str | None = None
    include_completed_goals: bool = False


class PlanFinalizeRequest(BaseModel):
    notes: str | None = None


class PlanSubmitRequest(BaseModel):
    supervisor_id: uuid.UUID | None = None
    comments: str | None = None


class PlanApproveRequest(BaseModel):
    comments: str | None = None


class PlanReturnRequest(BaseModel):
    reasons: str = Field(..., min_length=1, description="Actionable clinical feedback for return")


class PlanLockRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason for sealing plan")


class PlanUnlockRequest(BaseModel):
    justification: str = Field(..., min_length=10, description="Mandatory Director justification for unlocking sealed plan")


# ── Case Note Goal Linking Schemas ───────────────────────────────────
class ActiveGoalItem(BaseModel):
    id: uuid.UUID
    goal_text: str
    category: str | None = None
    target_date: date | None = None
    status: str
    plan_id: uuid.UUID
    plan_number: str
    plan_type: str
    plan_title: str
    activities: list[dict[str, Any]] = []


# ── Print Schemas ────────────────────────────────────────────────────
class PlanPrintResponse(BaseModel):
    plan_id: uuid.UUID
    plan_number: str
    plan_type: str
    title: str
    status: str
    version_number: int
    meeting_date: datetime | None = None
    meeting_location: str | None = None
    narrative: str | None = None
    document_hash: str | None = None
    case_number: str
    case_title: str
    client_name: str | None = None
    family_name: str | None = None
    participants: list[PlanParticipantResponse] = []
    concerns: list[PlanConcernResponse] = []
    strengths: list[PlanStrengthResponse] = []
    goals: list[PlanGoalResponse] = []
    signatures: list[PlanSignatureResponse] = []
    printed_at: datetime
    printed_by_name: str
