"""Client schemas matching the CRBCL case management platform."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class ClientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=200)
    last_name: str = Field(min_length=1, max_length=200)
    date_of_birth: date | None = None
    gender: str | None = None
    status: str = Field(default="Pending Intake", max_length=50)
    risk_level: str = Field(default="Low", max_length=20)
    phone: str | None = None
    email: EmailStr | str | None = None
    address: str | None = None
    city: str | None = None
    province: str = Field(default="Saskatchewan", max_length=100)
    indigenous_identity: str | None = None
    band_nation: str | None = None
    notes: str | None = None
    assigned_team_id: uuid.UUID | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    status: str | None = None
    risk_level: str | None = None
    phone: str | None = None
    email: EmailStr | str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    indigenous_identity: str | None = None
    band_nation: str | None = None
    notes: str | None = None
    assigned_team_id: uuid.UUID | None = None


class ClientResponse(ClientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    version: int = 1

    # Compatibility alias for frontend that expects created_date
    @property
    def created_date(self) -> str:
        return self.created_at.isoformat()

    model_config = {"from_attributes": True}
