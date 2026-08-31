"""Schemas for audit and access events."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    user_id: uuid.UUID | None = None
    timestamp: datetime
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    request_id: str | None = None
    source: str = "api"
    metadata_: dict | None = Field(default=None, alias="metadata")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AccessEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    user_id: uuid.UUID
    timestamp: datetime
    entity_type: str
    entity_id: uuid.UUID | None = None
    description: str = ""
    metadata_: dict | None = Field(default=None, alias="metadata")

    model_config = {"from_attributes": True, "populate_by_name": True}
