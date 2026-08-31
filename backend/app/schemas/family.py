"""Family schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class FamilyBase(BaseModel):
    family_name: str = Field(min_length=1, max_length=300)
    primary_contact_name: str | None = None
    primary_contact_phone: str | None = None
    primary_contact_email: EmailStr | str | None = None
    address: str | None = None
    city: str | None = None
    province: str = Field(default="Saskatchewan", max_length=100)
    status: str = Field(default="Active", max_length=50)
    risk_level: str = Field(default="Low", max_length=20)
    indigenous_identity: str | None = None
    band_nation: str | None = None
    total_members: int = Field(default=1, ge=1)
    notes: str | None = None
    assigned_team_id: uuid.UUID | None = None


class FamilyCreate(FamilyBase):
    pass


class FamilyUpdate(BaseModel):
    family_name: str | None = None
    primary_contact_name: str | None = None
    primary_contact_phone: str | None = None
    primary_contact_email: EmailStr | str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    status: str | None = None
    risk_level: str | None = None
    indigenous_identity: str | None = None
    band_nation: str | None = None
    total_members: int | None = None
    notes: str | None = None
    assigned_team_id: uuid.UUID | None = None


class FamilyResponse(FamilyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    version: int = 1

    model_config = {"from_attributes": True}
