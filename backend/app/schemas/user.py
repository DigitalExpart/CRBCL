"""User and team membership schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role_keys: list[str] = Field(default_factory=list)
    team_ids: list[uuid.UUID] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = None
    display_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role_keys: list[str] | None = None
    team_ids: list[uuid.UUID] | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    display_name: str | None = None
    phone: str | None = None
    is_active: bool
    is_verified: bool
    roles: list[str] = []
    team_access: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
