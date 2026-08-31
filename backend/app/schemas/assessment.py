"""Pydantic schemas for the Assessment Engine (Templates, Versions, Sections, Questions, Answers, Instances, Comparisons)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ── Question Option Schemas ─────────────────────────────────────────


class AssessmentQuestionOptionBase(BaseModel):
    key: str = Field(..., max_length=100)
    label: str = Field(..., max_length=255)
    description: str | None = None
    score_value: float | None = None
    sort_order: int = 0
    is_active: bool = True


class AssessmentQuestionOptionCreate(AssessmentQuestionOptionBase):
    pass


class AssessmentQuestionOptionUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    score_value: float | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class AssessmentQuestionOptionResponse(AssessmentQuestionOptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── Question Schemas ────────────────────────────────────────────────


class AssessmentQuestionBase(BaseModel):
    key: str = Field(..., max_length=100)
    label: str
    help_text: str | None = None
    question_type: str = Field(
        ..., max_length=50
    )  # BOOLEAN, SINGLE_SELECT, MULTI_SELECT, TEXT, LONG_TEXT, NUMBER, DATE, DATETIME, LOOKUP
    is_required: bool = False
    sort_order: int = 0
    is_reportable: bool = True
    validation_rules: dict[str, Any] | None = None
    visibility_condition: dict[str, Any] | None = None
    lookup_list_key: str | None = None


class AssessmentQuestionCreate(AssessmentQuestionBase):
    options: list[AssessmentQuestionOptionCreate] = []


class AssessmentQuestionUpdate(BaseModel):
    label: str | None = None
    help_text: str | None = None
    is_required: bool | None = None
    sort_order: int | None = None
    is_reportable: bool | None = None
    validation_rules: dict[str, Any] | None = None
    visibility_condition: dict[str, Any] | None = None
    lookup_list_key: str | None = None


class AssessmentQuestionResponse(AssessmentQuestionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    options: list[AssessmentQuestionOptionResponse] = []
    created_at: datetime
    updated_at: datetime


# ── Section Schemas ─────────────────────────────────────────────────


class AssessmentSectionBase(BaseModel):
    key: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    description: str | None = None
    sort_order: int = 0
    is_required: bool = False
    visibility_condition: dict[str, Any] | None = None


class AssessmentSectionCreate(AssessmentSectionBase):
    questions: list[AssessmentQuestionCreate] = []


class AssessmentSectionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_required: bool | None = None
    visibility_condition: dict[str, Any] | None = None


class AssessmentSectionResponse(AssessmentSectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_version_id: uuid.UUID
    questions: list[AssessmentQuestionResponse] = []
    created_at: datetime
    updated_at: datetime


# ── Template Version Schemas ────────────────────────────────────────


class AssessmentTemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template_id: uuid.UUID
    version_number: int
    status: str  # DRAFT, PUBLISHED, RETIRED
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    change_notes: str | None = None
    created_by: uuid.UUID | None = None
    published_by: uuid.UUID | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AssessmentTemplateVersionDetailResponse(AssessmentTemplateVersionResponse):
    sections: list[AssessmentSectionResponse] = []


class AssessmentTemplateVersionCreate(BaseModel):
    change_notes: str | None = None
    clone_from_version_id: uuid.UUID | None = None


# ── Template Schemas ────────────────────────────────────────────────


class AssessmentTemplateBase(BaseModel):
    key: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    description: str = ""
    category: str = "general"
    is_active: bool = True


class AssessmentTemplateCreate(AssessmentTemplateBase):
    initial_version_notes: str | None = "Initial draft version"


class AssessmentTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    is_active: bool | None = None


class AssessmentTemplateResponse(AssessmentTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    published_version: AssessmentTemplateVersionResponse | None = None


class AssessmentTemplateDetailResponse(AssessmentTemplateResponse):
    versions: list[AssessmentTemplateVersionResponse] = []
    active_version: AssessmentTemplateVersionDetailResponse | None = None


# ── Answer Schemas ──────────────────────────────────────────────────


class AssessmentAnswerItem(BaseModel):
    question_id: uuid.UUID | None = None
    question_key: str | None = None
    boolean_value: bool | None = None
    number_value: float | None = None
    text_value: str | None = None
    date_value: date | None = None
    datetime_value: datetime | None = None
    json_value: dict[str, Any] | list[Any] | None = None
    selected_option_ids: list[uuid.UUID] = []
    selected_option_keys: list[str] = []
    notes: str | None = None


class AssessmentAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    question_id: uuid.UUID
    question_key: str | None = None
    boolean_value: bool | None = None
    number_value: float | None = None
    text_value: str | None = None
    date_value: date | None = None
    datetime_value: datetime | None = None
    json_value: Any = None
    notes: str | None = None
    selected_option_ids: list[uuid.UUID] = []
    selected_options: list[AssessmentQuestionOptionResponse] = []
    created_at: datetime
    updated_at: datetime


class AssessmentAnswersSaveRequest(BaseModel):
    answers: list[AssessmentAnswerItem]
    determination: str | None = None
    determination_notes: str | None = None
    summary: str | None = None


# ── Assessment Instance Schemas ─────────────────────────────────────


class AssessmentCreate(BaseModel):
    case_id: uuid.UUID
    template_key: str
    template_version_id: uuid.UUID | None = None  # Defaults to active published version
    person_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    household_id: uuid.UUID | None = None
    title: str | None = None
    conducted_at: datetime | None = None
    summary: str | None = None
    metadata_: dict[str, Any] | None = None


class AssessmentUpdate(BaseModel):
    title: str | None = None
    conducted_at: datetime | None = None
    determination: str | None = None
    determination_notes: str | None = None
    summary: str | None = None
    metadata_: dict[str, Any] | None = None


class AssessmentCompleteRequest(BaseModel):
    determination: str
    determination_notes: str | None = None
    action_recommendations: str | None = None
    summary: str | None = None
    clinical_summary: str | None = None

    @model_validator(mode="after")
    def populate_aliases(self) -> AssessmentCompleteRequest:
        if self.clinical_summary and not self.summary:
            self.summary = self.clinical_summary
        if self.action_recommendations and not self.determination_notes:
            self.determination_notes = self.action_recommendations
        return self


class AssessmentLockRequest(BaseModel):
    reason: str | None = "Assessment finalized and locked."


class AssessmentUnlockRequest(BaseModel):
    reason: str | None = None
    justification: str | None = None

    @model_validator(mode="after")
    def check_reason_or_justification(self) -> AssessmentUnlockRequest:
        final_reason = self.reason or self.justification
        if not final_reason or len(final_reason.strip()) < 5:
            raise ValueError("A mandatory justification of at least 5 characters is required.")
        self.reason = final_reason.strip()
        return self


class AssessmentReassignRequest(BaseModel):
    target_case_id: uuid.UUID
    target_family_id: uuid.UUID | None = None
    target_household_id: uuid.UUID | None = None
    target_person_id: uuid.UUID | None = None
    reason: str = Field(..., min_length=5, description="Mandatory clinical/administrative reason for case reassignment")


class AssessmentStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    from_status: str | None = None
    to_status: str
    reason: str | None = None
    created_by: uuid.UUID
    author_name: str | None = None
    created_at: datetime


class AssessmentUnlockEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    unlocked_by: uuid.UUID
    director_name: str | None = None
    reason: str
    unlocked_at: datetime


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str | None = None
    person_id: uuid.UUID | None = None
    person_name: str | None = None
    client_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    family_name: str | None = None
    household_id: uuid.UUID | None = None
    template_id: uuid.UUID
    template_key: str | None = None
    template_name: str | None = None
    template_category: str | None = None
    template_version_id: uuid.UUID
    version_number: int | None = None
    assessment_number: str
    title: str
    status: str
    determination: str | None = None
    determination_notes: str | None = None
    conducted_by: uuid.UUID
    conducted_by_name: str | None = None
    conducted_at: datetime
    completed_at: datetime | None = None
    completed_by: uuid.UUID | None = None
    locked_at: datetime | None = None
    locked_by: uuid.UUID | None = None
    is_locked: bool = False
    summary: str | None = None
    metadata_: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class AssessmentDetailResponse(AssessmentResponse):
    template_version: AssessmentTemplateVersionDetailResponse | None = None
    answers: list[AssessmentAnswerResponse] = []
    status_history: list[AssessmentStatusHistoryResponse] = []
    unlock_events: list[AssessmentUnlockEventResponse] = []
    indicator_summary: dict[str, Any] | None = None


# ── Comparison Schemas ──────────────────────────────────────────────


class AssessmentComparisonQuestionValue(BaseModel):
    assessment_id: uuid.UUID
    conducted_at: datetime
    answer_display: str | None = None
    boolean_value: bool | None = None
    number_value: float | None = None
    text_value: str | None = None
    date_value: date | None = None
    selected_option_labels: list[str] = []


class AssessmentComparisonQuestion(BaseModel):
    question_id: uuid.UUID
    question_key: str
    label: str
    section_title: str
    question_type: str
    is_changed: bool = False
    values: list[AssessmentComparisonQuestionValue] = []


class AssessmentComparisonResponse(BaseModel):
    template_key: str
    template_name: str
    assessments: list[AssessmentResponse] = []
    questions: list[AssessmentComparisonQuestion] = []
    summary_deltas: dict[str, Any] = {}
