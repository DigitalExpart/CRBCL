"""Audit and access logging service."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AccessEvent, AuditEvent

SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "refresh_token", "secret", "session_secret"}


def _sanitize_dict(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return data
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_dict(v)
        elif isinstance(v, Decimal):
            sanitized[k] = float(v)
        elif isinstance(v, uuid.UUID | date | datetime):
            sanitized[k] = str(v)
        elif isinstance(v, list):
            sanitized[k] = [
                float(item)
                if isinstance(item, Decimal)
                else str(item)
                if isinstance(item, uuid.UUID | date | datetime)
                else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized



class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        before_data: dict | None = None,
        after_data: dict | None = None,
        metadata: dict | None = None,
        request_id: str | None = None,
        session_id: uuid.UUID | None = None,
        source: str = "api",
        ip_address: str | None = None,
    ) -> AuditEvent:
        """Create an append-only audit event. Never logs credentials or secrets."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            before_data=_sanitize_dict(before_data),
            after_data=_sanitize_dict(after_data),
            metadata_=_sanitize_dict(metadata),
            request_id=request_id,
            session_id=session_id,
            source=source,
            ip_address=ip_address,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    log = log_event


    async def log_access(
        self,
        event_type: str,
        user_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        description: str = "",
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> AccessEvent:
        """Create an explicit application-level access event for sensitive reads."""
        event = AccessEvent(
            event_type=event_type,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata_=_sanitize_dict(metadata),
            ip_address=ip_address,
        )
        self.db.add(event)
        await self.db.flush()
        return event
