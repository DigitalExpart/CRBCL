"""User and team membership schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator

from app.constants.department import DEPARTMENTS


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    department: str | None = None
    role_keys: list[str] = Field(default_factory=list)
    team_ids: list[uuid.UUID] = Field(default_factory=list)


    @validator("department")
    def department_must_be_known(cls, v):
        if v is not None and v not in DEPARTMENTS:
            raise ValueError("Invalid department")
        return v

class UserUpdate(BaseModel):
    full_name: str | None = None
    display_name: str | None = None
    phone: str | None = None
    department: str | None = None
    is_active: bool | None = None
    role: str | None = None
    role_keys: list[str] | None = None
    team_access: list[str] | None = None
    team_ids: list[uuid.UUID] | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    display_name: str | None = None
    phone: str | None = None
    department: str | None = None
    is_active: bool
    is_verified: bool
    roles: list[str] = []
    team_access: list[str] = []
    requested_role: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppearancePreferences(BaseModel):
    theme_mode: str = Field(default="system", description="light | dark | system")
    accent_theme: str = Field(
        default="crbcl",
        description="crbcl | burgundy | earth | forest | prairie | ocean | teal | neutral | pink | light-pink | purple | light-purple | sky-blue | yellow",
    )
    density: str = Field(default="comfortable", description="comfortable | compact")
    sidebar_collapsed: bool = Field(default=False)
    card_radius: str = Field(default="rounded", description="rounded | subtle")
    reduced_motion: bool = Field(default=False)
    high_contrast: bool = Field(default=False)
    default_landing_dashboard: str | None = Field(default=None, max_length=60)

    @validator("theme_mode")
    def validate_theme_mode(cls, v):
        allowed = {"light", "dark", "system"}
        if v not in allowed:
            raise ValueError(f"Invalid theme_mode: {v}. Must be one of {allowed}")
        return v

    @validator("accent_theme")
    def validate_accent_theme(cls, v):
        if isinstance(v, str):
            v = v.lower().strip().replace("_", "-")
        allowed = {
            "crbcl",
            "burgundy",
            "earth",
            "forest",
            "prairie",
            "ocean",
            "teal",
            "neutral",
            "pink",
            "light-pink",
            "purple",
            "light-purple",
            "sky-blue",
            "yellow",
        }
        if v not in allowed:
            raise ValueError(f"Invalid accent_theme: {v}. Must be one of {allowed}")
        return v

    @validator("density")
    def validate_density(cls, v):
        allowed = {"comfortable", "compact"}
        if v not in allowed:
            raise ValueError(f"Invalid density: {v}. Must be one of {allowed}")
        return v

    @validator("card_radius")
    def validate_card_radius(cls, v):
        allowed = {"rounded", "subtle"}
        if v not in allowed:
            raise ValueError(f"Invalid card_radius: {v}. Must be one of {allowed}")
        return v

    @validator("default_landing_dashboard")
    def validate_dashboard_path(cls, v):
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.startswith("/") or v.startswith("//") or ".." in v:
            raise ValueError("Invalid landing dashboard path: must be relative root path")
        if any(c in v for c in "<>'\"\\;`\n\r"):
            raise ValueError("Disallowed characters in landing dashboard path")
        return v


class UserPreferencesPayload(BaseModel):
    appearance: AppearancePreferences = Field(default_factory=AppearancePreferences)
    dashboard_widgets: list[dict[str, object]] | None = None

    model_config = {"extra": "forbid"}


class UserPreferencesResponse(BaseModel):
    appearance: AppearancePreferences
    dashboard_widgets: list[dict[str, object]] = []
