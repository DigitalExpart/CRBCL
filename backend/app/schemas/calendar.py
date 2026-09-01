"""Pydantic schemas for Calendar and Scheduling operations."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CalendarRecurrenceRuleBase(BaseModel):
    frequency: str = "WEEKLY"  # DAILY, WEEKLY, BIWEEKLY, MONTHLY
    interval: int = 1
    by_weekday: str | None = None  # "MO,WE,FR"
    until_date: date | None = None
    max_occurrences: int | None = None


class CalendarRecurrenceRuleCreate(CalendarRecurrenceRuleBase):
    pass


class CalendarRecurrenceRuleResponse(CalendarRecurrenceRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    calendar_event_id: uuid.UUID
    created_at: datetime


class CalendarEventBase(BaseModel):
    event_type: str = "APPOINTMENT"
    title: str = Field(..., min_length=1, max_length=255)
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    timezone: str = "America/Regina"
    location: str | None = None
    description: str | None = None
    source_entity_type: str | None = None
    source_entity_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    assigned_user_id: uuid.UUID | None = None
    status: str = "SCHEDULED"


class CalendarEventCreate(CalendarEventBase):
    recurrence: CalendarRecurrenceRuleCreate | None = None


class CalendarEventUpdate(BaseModel):
    title: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: str | None = None
    description: str | None = None
    assigned_user_id: uuid.UUID | None = None
    status: str | None = None


class CalendarEventResponse(CalendarEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None

    # Redaction flag for client UI
    is_redacted: bool = False

    # Optional nested details for rich display
    assigned_user_name: str | None = None
    case_number: str | None = None
    person_name: str | None = None
    recurrence_rule: CalendarRecurrenceRuleResponse | None = None


class MyScheduleFilter(BaseModel):
    start_at: datetime
    end_at: datetime
    event_types: list[str] | None = None


class TeamScheduleFilter(BaseModel):
    start_at: datetime
    end_at: datetime
    team_id: uuid.UUID | None = None
    worker_ids: list[uuid.UUID] | None = None
    event_types: list[str] | None = None
