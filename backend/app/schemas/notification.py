"""Pydantic schemas for Notifications, Preferences, Deliveries, and Templates."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    recipient_id: uuid.UUID
    type: str
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    related_entity_type: str | None = None
    related_entity_id: uuid.UUID | None = None
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, URGENT


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferenceBase(BaseModel):
    event_type: str
    in_app_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    is_mandatory: bool = False


class NotificationPreferenceUpdate(BaseModel):
    event_type: str
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notification_id: uuid.UUID | None = None
    channel: str
    provider: str
    status: str
    recipient_address: str
    attempt_count: int
    max_attempts: int
    last_attempt_at: datetime | None = None
    sent_at: datetime | None = None
    failed_at: datetime | None = None
    failure_code: str | None = None
    error_message: str | None = None
    idempotency_key: str
    created_at: datetime


class NotificationTemplateBase(BaseModel):
    event_type: str
    channel: str
    title_template: str = Field(..., min_length=1, max_length=255)
    body_template: str
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    title_template: str | None = None
    body_template: str | None = None
    is_active: bool | None = None


class NotificationTemplateResponse(NotificationTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
