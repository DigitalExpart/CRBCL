"""Test suite for Outbox delivery processing, retry mechanism, and delivery failure isolation."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.worker import process_event
from app.models.case import Case
from app.models.notification import Notification, NotificationDelivery
from app.services.notification_providers import DeliveryResult, EmailProvider
from app.services.notification_service import NotificationService


class FailingEmailProvider(EmailProvider):
    """Simulated provider that fails initially."""

    def __init__(self):
        self.should_fail = True

    async def send_email(
        self, to_address: str, subject: str, body_text: str, body_html: str | None = None
    ) -> DeliveryResult:
        if self.should_fail:
            return DeliveryResult(
                success=False,
                status="FAILED",
                provider="FAILING_PROVIDER",
                failure_code="SMTP_TIMEOUT",
                error_message="Connection timed out",
            )
        return DeliveryResult(success=True, status="SENT", provider="FAILING_PROVIDER")


@pytest.mark.asyncio
async def test_outbox_notification_dispatch_and_retry_flow(
    client: AsyncClient, db_session: AsyncSession, it_admin_user, caseworker_user, seed_roles_and_permissions
):
    """Verify background outbox dispatch, provider failure isolation, and manual retry command."""
    cw_user = caseworker_user["user"]
    admin_headers = it_admin_user["headers"]

    # 1. Create a case
    case = Case(
        case_number="CAS-NOTIF-001",
        title="Delivery Integration Test Case",
        status="Open",
        stage="INVESTIGATION",
        assigned_worker_id=cw_user.id,
    )
    db_session.add(case)
    await db_session.flush()
    await db_session.commit()

    # 2. Simulate background worker processing a case note event with notification flag
    note_id = uuid.uuid4()
    await process_event(
        session=db_session,
        event_type="CASE_NOTE_CREATED",
        aggregate_type="case_note",
        aggregate_id=str(note_id),
        payload={
            "case_id": str(case.id),
            "note_id": str(note_id),
            "subject": "Urgent Caregiver Discussion",
            "author": "Supervisor Smith",
            "notify_team": True,
        },
    )
    await db_session.commit()

    # 3. Verify notification created for assigned worker
    stmt = select(Notification).where(
        Notification.recipient_id == cw_user.id,
        Notification.type == "CASE_NOTE_ADDED",
    )
    res = await db_session.execute(stmt)
    notif = res.scalar_one_or_none()
    assert notif is not None
    assert "Urgent Caregiver Discussion" in notif.message

    # 4. Test provider failure and retry command
    failing_provider = FailingEmailProvider()
    notif_svc = NotificationService(db_session, email_provider=failing_provider)

    dispatch_res = await notif_svc.notify_user(
        recipient_id=cw_user.id,
        event_type="APPOINTMENT_REMINDER",
        title="Test Failed Delivery",
        message="This message will fail on initial attempt.",
        recipient_email=cw_user.email,
        idempotency_key_prefix="TEST_FAIL_01",
    )
    await db_session.commit()

    deliveries = dispatch_res["deliveries"]
    assert len(deliveries) > 0
    failed_deliv = deliveries[0]
    assert failed_deliv.status == "FAILED"
    assert failed_deliv.failure_code == "SMTP_TIMEOUT"

    # 5. Now fix provider and trigger technical retry command via API
    failing_provider.should_fail = False
    notif_svc.email_provider = failing_provider

    retry_res = await client.post(
        f"/api/v1/notifications/deliveries/{failed_deliv.id}/retry",
        headers=admin_headers,
    )
    assert retry_res.status_code == 200
    retried_data = retry_res.json()
    assert retried_data["status"] == "SENT"
    assert retried_data["attempt_count"] == 2
