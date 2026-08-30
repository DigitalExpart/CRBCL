"""Team schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    short_name: str = Field(default="", max_length=100)
    description: str = Field(default="")
    color: str = Field(default="bg-slate-700", max_length=30)
    sort_order: int = 0
    is_active: bool = True


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    short_name: str | None = None
    description: str | None = None
    color: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class TeamResponse(TeamBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
