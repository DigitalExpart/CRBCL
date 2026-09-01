"""Pydantic schemas for Staffing Facilitator domain."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StaffingAttendeeBase(BaseModel):
    user_id: uuid.UUID
    attendance_status: str = "PENDING"  # ATTENDED, ABSENT, EXCUSED, PENDING
    notes: str | None = None


class StaffingAttendeeCreate(StaffingAttendeeBase):
    pass


class StaffingAttendeeUpdate(BaseModel):
    attendance_status: str | None = None
    notes: str | None = None


class StaffingAttendeeResponse(StaffingAttendeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime
    user_name: str | None = None
    user_email: str | None = None


class StaffingCaseBase(BaseModel):
    case_id: uuid.UUID
    review_status: str = "PENDING"  # PENDING, REVIEWED, DEFERRED, ESCALATED
    discussion_summary: str | None = None
    follow_up_required: bool = False
    follow_up_date: date | None = None
    assigned_worker_id: uuid.UUID | None = None


class StaffingCaseAdd(StaffingCaseBase):
    pass


class StaffingCaseUpdate(BaseModel):
    review_status: str | None = None
    discussion_summary: str | None = None
    follow_up_required: bool | None = None
    follow_up_date: date | None = None
    assigned_worker_id: uuid.UUID | None = None


class StaffingCaseResponse(StaffingCaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime
    case_number: str | None = None
    case_title: str | None = None
    assigned_worker_name: str | None = None


class StaffingSessionBase(BaseModel):
    session_date: datetime
    title: str = Field(..., min_length=1, max_length=255)
    facilitator_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    cadence: str = "WEEKLY"  # WEEKLY, BIWEEKLY, MONTHLY, AD_HOC
    status: str = "SCHEDULED"  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    location: str | None = None
    minutes: str | None = None


class StaffingSessionCreate(StaffingSessionBase):
    attendee_ids: list[uuid.UUID] | None = None
    case_ids: list[uuid.UUID] | None = None


class StaffingSessionUpdate(BaseModel):
    session_date: datetime | None = None
    title: str | None = None
    facilitator_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    cadence: str | None = None
    status: str | None = None
    location: str | None = None
    minutes: str | None = None


class StaffingSessionResponse(StaffingSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    facilitator_name: str | None = None
    team_name: str | None = None
    attendees_count: int = 0
    cases_count: int = 0
    attendees: list[StaffingAttendeeResponse] = []
    cases: list[StaffingCaseResponse] = []


class StaffingCaseBucketItem(BaseModel):
    case_id: uuid.UUID
    case_number: str
    case_title: str
    stage: str
    status: str
    assigned_worker_name: str | None = None
    last_staffed_date: datetime | None = None
    days_since_last_staffed: int | None = None
    opened_date: date | None = None
    months_open: int | None = None
    risk_level: str | None = None
    last_case_note_date: datetime | None = None


class StaffingCaseBucketsResponse(BaseModel):
    not_staffed_90_days: list[StaffingCaseBucketItem] = []
    open_12_months: list[StaffingCaseBucketItem] = []
    high_risk: list[StaffingCaseBucketItem] = []
    missing_recent_note: list[StaffingCaseBucketItem] = []
