"""Background worker for outbox event processing and scheduled reminder execution."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.case import Case
from app.services.notification_service import NotificationService
from app.services.reminder_service import ScheduledReminderService
from app.workflows.outbox import OutboxService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crbcl.worker")


async def process_event(
    session,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
) -> None:
    """
    Handler dispatcher for background events.
    Translates domain events into in-app notifications and outbound deliveries.
    """
    logger.info(
        "Processing outbox event: type=%s aggregate=%s id=%s",
        event_type,
        aggregate_type,
        aggregate_id,
    )
    notif_svc = NotificationService(session)

    try:
        if event_type == "CASE_NOTE_CREATED" and payload.get("notify_team"):
            case_id_str = payload.get("case_id")
            if case_id_str:
                case_res = await session.execute(select(Case).where(Case.id == uuid.UUID(case_id_str)))
                case = case_res.scalar_one_or_none()
                if case and case.assigned_worker_id:
                    await notif_svc.notify_user(
                        recipient_id=case.assigned_worker_id,
                        event_type="CASE_NOTE_ADDED",
                        title=f"New Case Note on {case.case_number}",
                        message=f"A progress note '{payload.get('subject')}' was recorded by {payload.get('author')}.",
                        related_entity_type="case_note",
                        related_entity_id=uuid.UUID(aggregate_id),
                    )

        elif event_type == "court_event.created":
            case_id_str = payload.get("case_id")
            if case_id_str:
                case_res = await session.execute(select(Case).where(Case.id == uuid.UUID(case_id_str)))
                case = case_res.scalar_one_or_none()
                if case and case.assigned_worker_id:
                    await notif_svc.notify_user(
                        recipient_id=case.assigned_worker_id,
                        event_type="COURT_REMINDER",
                        title="Court Hearing Scheduled",
                        message=f"A {payload.get('hearing_type', 'hearing')} is scheduled for case {case.case_number} on {payload.get('hearing_date')}.",
                        related_entity_type="court_event",
                        related_entity_id=uuid.UUID(aggregate_id),
                    )
    except Exception as e:
        logger.warning("Error in event notification dispatcher: %s", e)


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
                            session=session,
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


async def run_scheduled_reminders_loop(check_interval: float = 3600.0) -> None:
    """Scheduled cron loop for automated reminders."""
    logger.info("Starting CRBCL Scheduled Reminders Loop...")
    while True:
        try:
            async with async_session_factory() as session:
                reminder_svc = ScheduledReminderService(session)
                results = await reminder_svc.run_all_reminder_jobs()
                await session.commit()
                logger.info("Scheduled reminders executed: %s", results)
        except Exception as exc:
            logger.error("Error in scheduled reminders loop: %s", exc)

        await asyncio.sleep(check_interval)


async def main() -> None:
    await asyncio.gather(
        run_scheduled_reminders_loop(),
        run_outbox_processor_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
