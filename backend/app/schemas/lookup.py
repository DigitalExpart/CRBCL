"""Lookup schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LookupValueResponse(BaseModel):
    id: uuid.UUID
    key: str
    label: str
    description: str | None = ""
    sort_order: int = 0
    is_active: bool = True
    metadata_: dict | None = Field(default=None)

    model_config = {"from_attributes": True}


class LookupListResponse(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None = ""
    is_active: bool = True
    values: list[LookupValueResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
