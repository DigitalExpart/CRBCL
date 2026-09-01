"""Teams Notification Delivery Service integrated with Phase 9 Outbox System."""

import logging
from typing import Any

from app.services.integrations.gateway import IntegrationGateway
from app.services.integrations.m365.base import MicrosoftProvider
from app.services.integrations.m365.fake_provider import FakeMicrosoftProvider

logger = logging.getLogger(__name__)


async def send_teams_alert(
    channel_id: str,
    raw_message: str,
    provider: MicrosoftProvider | None = None,
) -> dict[str, Any]:
    """Send privacy-safe notification alert to Microsoft Teams channel.

    Guarantees:
    - Strips narrative PII/PHI via IntegrationGateway.sanitize_teams_message.
    - Safe error handling.
    """
    if provider is None:
        provider = FakeMicrosoftProvider()

    sanitized_text = IntegrationGateway.sanitize_teams_message(raw_message)

    try:
        res = await provider.send_teams_notification(channel_id, sanitized_text)
        return {"status": "DELIVERED", "teams_message_id": res.get("id")}
    except Exception as exc:
        logger.error(f"Failed to deliver Teams notification to channel {channel_id}: {exc}")
        return {"status": "FAILED", "error": str(exc)}
