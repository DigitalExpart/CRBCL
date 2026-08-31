"""Case note schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CaseNoteBase(BaseModel):
    subject: str = Field(default="", max_length=500)
    content: str = Field(min_length=1)
    note_type: str = Field(default="Progress Note", max_length=50)
    is_confidential: bool = False
    author_name: str | None = None


class CaseNoteCreate(CaseNoteBase):
    case_id: uuid.UUID


class CaseNoteUpdate(BaseModel):
    subject: str | None = None
    content: str | None = None
    note_type: str | None = None
    is_confidential: bool | None = None


class CaseNoteResponse(CaseNoteBase):
    id: uuid.UUID
    case_id: uuid.UUID
    is_locked: bool = False
    locked_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    version: int = 1

    @property
    def created_date(self) -> str:
        return self.created_at.isoformat()

    model_config = {"from_attributes": True}
