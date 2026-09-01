"""Test suite for In-App Notifications, Unread Counts, and User Preferences."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPreference
from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_notification_lifecycle_unread_count_and_mark_read(
    client: AsyncClient, db_session: AsyncSession, caseworker_user, seed_roles_and_permissions
):
    """Verify in-app notification creation, unread count badge, mark as read, and mark all as read."""
    headers = caseworker_user["headers"]
    user = caseworker_user["user"]
    notif_svc = NotificationService(db_session)

    # 1. Initially unread count is 0
    cnt_res1 = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res1.status_code == 200
    assert cnt_res1.json()["unread_count"] == 0

    # 2. Trigger 2 in-app notifications
    res1 = await notif_svc.notify_user(
        recipient_id=user.id,
        event_type="INTAKE_DECISION",
        title="Intake Decision Approved",
        message="Supervisor approved intake referral REF-2026-004.",
    )
    res2 = await notif_svc.notify_user(
        recipient_id=user.id,
        event_type="APPOINTMENT_REMINDER",
        title="Upcoming Appointment",
        message="Client consultation scheduled for tomorrow at 10:00 AM.",
    )
    await db_session.commit()

    # 3. Verify unread count is now 2
    cnt_res2 = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res2.status_code == 200
    assert cnt_res2.json()["unread_count"] == 2

    # 4. List notifications
    list_res = await client.get("/api/v1/notifications?is_read=false", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) == 2
    first_notif_id = items[0]["id"]

    # 5. Mark first notification as read
    read_res = await client.post(f"/api/v1/notifications/{first_notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Verify unread count decremented to 1
    cnt_res3 = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res3.json()["unread_count"] == 1

    # 6. Mark all as read
    all_res = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert all_res.status_code == 200

    # Verify unread count is now 0
    cnt_res4 = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res4.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_notification_preferences_and_mandatory_locks(
    client: AsyncClient, db_session: AsyncSession, caseworker_user, seed_roles_and_permissions
):
    """Verify user notification preferences can be customized while mandatory compliance alerts remain locked."""
    headers = caseworker_user["headers"]

    # 1. Fetch preferences (seeds defaults)
    pref_res = await client.get("/api/v1/notification-preferences", headers=headers)
    assert pref_res.status_code == 200
    prefs = pref_res.json()
    assert len(prefs) > 0

    # 2. Update a non-mandatory preference (disable email for APPOINTMENT_REMINDER)
    update_res = await client.patch(
        "/api/v1/notification-preferences",
        json={
            "event_type": "APPOINTMENT_REMINDER",
            "email_enabled": False,
            "sms_enabled": True,
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_pref = update_res.json()
    assert updated_pref["event_type"] == "APPOINTMENT_REMINDER"
    assert updated_pref["email_enabled"] is False
    assert updated_pref["sms_enabled"] is True

    # 3. Attempting to disable email on a MANDATORY compliance notification (COURT_REMINDER) preserves compliance enforcement
    mand_res = await client.patch(
        "/api/v1/notification-preferences",
        json={
            "event_type": "COURT_REMINDER",
            "email_enabled": False,
            "in_app_enabled": False,
        },
        headers=headers,
    )
    assert mand_res.status_code == 200
    mand_data = mand_res.json()
    assert mand_data["is_mandatory"] is True
    # Mandatory enforcement keeps in_app and email enabled
    assert mand_data["in_app_enabled"] is True
    assert mand_data["email_enabled"] is True
