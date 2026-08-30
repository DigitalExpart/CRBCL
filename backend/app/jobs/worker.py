"""Background worker for outbox event processing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.workflows.outbox import OutboxService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crbcl.worker")


async def process_event(event_type: str, aggregate_type: str, aggregate_id: str, payload: dict[str, Any]) -> None:
    """
    Handler dispatcher for background events.
    In Phase 1, logs processing safely without exposing secrets.
    Future phases attach email, notifications, and integration adapters here.
    """
    logger.info(
        "Processing outbox event: type=%s aggregate=%s id=%s",
        event_type,
        aggregate_type,
        aggregate_id,
    )
    # Simulate processing delay if needed
    await asyncio.sleep(0.01)


async def run_outbox_processor_loop(poll_interval: float = 2.0) -> None:
    """Continuous polling loop for outbox events."""
    logger.info("Starting CRBCL Outbox Background Worker...")
    while True:
        try:
            async with async_session_factory() as session:
                outbox_service = OutboxService(session)
                events = await outbox_service.get_pending_events(limit=10)

                for event in events:
                    try:
                        await process_event(
                            event_type=event.event_type,
                            aggregate_type=event.aggregate_type,
                            aggregate_id=str(event.aggregate_id),
                            payload=event.payload,
                        )
                        await outbox_service.mark_processed(event.id)
                    except Exception as exc:
                        logger.error("Failed processing outbox event %s: %s", event.id, exc)
                        await outbox_service.record_failure(event.id, str(exc))

                await session.commit()
        except Exception as exc:
            logger.error("Error in outbox processing loop: %s", exc)

        await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_outbox_processor_loop())
