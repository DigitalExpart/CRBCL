"""Pydantic schemas for authentication requests and responses."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class RegisterResponse(BaseModel):
    success: bool = True
    message: str = "Registration successful"
    user_id: uuid.UUID


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    success: bool = True
    message: str = ""


class UserInfo(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    display_name: str | None = None
    is_active: bool
    roles: list[str] = []
    permissions: list[str] = []
    team_access: list[str] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
