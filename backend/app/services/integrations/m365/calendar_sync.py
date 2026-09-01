"""Outbound Outlook Calendar Synchronization Service with Idempotency & Failure Isolation."""

import logging
import uuid
from datetime import datetime
from typing import Any

from app.models.calendar import CalendarEvent
from app.models.integrations import IntegrationExternalLink
from app.services.integrations.gateway import IntegrationGateway
from app.services.integrations.m365.base import MicrosoftProvider
from app.services.integrations.m365.fake_provider import FakeMicrosoftProvider
from app.services.integrations.utils import db_commit, db_query_first

logger = logging.getLogger(__name__)


async def sync_calendar_event_to_outlook(
    db: Any,
    event_id: uuid.UUID,
    provider: MicrosoftProvider | None = None,
) -> dict[str, Any]:
    """Sync internal CRBCL calendar event to external Microsoft Outlook calendar.

    Guarantees:
    - Data minimization: PII stripped via IntegrationGateway.
    - Idempotency: Checks integration_external_links to update existing external event instead of creating duplicates.
    - Failure Isolation: Internal CRBCL database changes remain intact if Outlook sync fails.
    """
    event = await db_query_first(db, CalendarEvent, CalendarEvent.id == event_id)
    if not event:
        raise ValueError(f"Calendar event {event_id} not found.")

    if provider is None:
        provider = FakeMicrosoftProvider()

    # Data minimization step
    minimized_payload = IntegrationGateway.minimize_calendar_payload(
        event_title=event.title or "Case Meeting",
        event_type=getattr(event, "event_type", "APPOINTMENT"),
    )
    minimized_payload["start"] = (
        event.start_at.isoformat() if getattr(event, "start_at", None) else datetime.utcnow().isoformat()
    )
    minimized_payload["end"] = (
        event.end_at.isoformat() if getattr(event, "end_at", None) else datetime.utcnow().isoformat()
    )

    # Check idempotency link
    link = await db_query_first(
        db,
        IntegrationExternalLink,
        IntegrationExternalLink.provider_key == "M365",
        IntegrationExternalLink.entity_type == "CALENDAR_EVENT",
        IntegrationExternalLink.internal_entity_id == event.id,
    )

    is_update = link is not None

    try:
        if is_update:
            # Idempotent update
            res = await provider.update_calendar_event(link.external_entity_id, minimized_payload)
            link.sync_status = "SYNCED"
            link.last_synced_at = datetime.utcnow()
            link.etag = res.get("etag")
        else:
            # First-time outbound push
            res = await provider.create_calendar_event(minimized_payload)
            link = IntegrationExternalLink(
                provider_key="M365",
                entity_type="CALENDAR_EVENT",
                internal_entity_id=event.id,
                external_entity_id=res["id"],
                sync_status="SYNCED",
                etag=res.get("etag"),
            )
            db.add(link)

        await db_commit(db)
        return {"status": "SUCCESS", "external_event_id": link.external_entity_id, "is_update": is_update}
    except Exception as exc:
        logger.error(f"Failed to sync calendar event {event.id} to M365: {exc}")
        if link:
            link.sync_status = "ERROR"
            await db_commit(db)
        return {"status": "FAILED", "error": str(exc)}
