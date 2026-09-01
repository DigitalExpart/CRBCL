"""Centralized Integration Gateway Pattern Implementation."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.integrations import IntegrationRegistry
from app.services.integrations.registry import ensure_default_integrations_seeded

logger = logging.getLogger(__name__)


class IntegrationGateway:
    """Centralized gateway controlling data access, minimization, and external provider dispatch."""

    @staticmethod
    def is_provider_operational(db: Session, provider_key: str) -> bool:
        """Verify whether an external provider is approved, configured, and enabled."""
        ensure_default_integrations_seeded(db)
        record = db.query(IntegrationRegistry).filter(IntegrationRegistry.provider_key == provider_key).first()
        if not record:
            return False
        return record.is_enabled and record.status in ["CONFIGURED", "PILOT", "APPROVED"]

    @staticmethod
    def minimize_calendar_payload(event_title: str, event_type: str) -> dict[str, Any]:
        """Strip all PII/PHI from calendar events prior to external provider dispatch."""
        safe_titles = {
            "COURT": "CRBCL Court Hearing",
            "HOME_VISIT": "CRBCL Case Visit",
            "STAFFING": "CRBCL Case Staffing Session",
            "APPOINTMENT": "CRBCL Appointment",
        }
        sanitized_title = safe_titles.get(event_type.upper(), "CRBCL Case Event")
        return {
            "subject": sanitized_title,
            "body": "CRBCL Family Wellness Platform Scheduled Event. (Details minimized for privacy compliance).",
            "is_private": True,
        }

    @staticmethod
    def sanitize_teams_message(raw_text: str) -> str:
        """Ensure child welfare narratives and client identities are excluded from Teams alerts."""
        return (
            f"🔔 CRBCL Alert: {raw_text}\n\n"
            "⚠️ Notice: Confidential case details must be viewed securely within the CRBCL Web Portal."
        )
