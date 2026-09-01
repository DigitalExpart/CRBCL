"""Notification domain service orchestrating preferences, in-app alerts, delivery channels, and templates."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationDelivery, NotificationPreference
from app.models.user import User
from app.repositories.notification_repo import NotificationRepo
from app.services.notification_providers import (
    ConsoleEmailProvider,
    ConsoleSmsProvider,
    EmailProvider,
    SmsProvider,
    sanitize_external_message,
)

logger = logging.getLogger("crbcl.notifications")


class NotificationService:
    """Core notification service for in-app alerts and multi-channel external dispatches."""

    def __init__(
        self,
        db: AsyncSession,
        email_provider: EmailProvider | None = None,
        sms_provider: SmsProvider | None = None,
    ):
        self.db = db
        self.repo = NotificationRepo(db)
        self.email_provider = email_provider or ConsoleEmailProvider()
        self.sms_provider = sms_provider or ConsoleSmsProvider()

    async def notify_user(
        self,
        recipient_id: uuid.UUID,
        event_type: str,
        title: str,
        message: str,
        related_entity_type: str | None = None,
        related_entity_id: uuid.UUID | None = None,
        priority: str = "NORMAL",
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
        idempotency_key_prefix: str | None = None,
        sms_consent: bool = False,
    ) -> dict[str, Any]:
        """
        Orchestrate multi-channel notification according to recipient preferences and compliance rules.
        """
        # Fetch or initialize preference
        pref = await self.repo.get_preference_for_event(recipient_id, event_type)
        in_app_ok = pref.in_app_enabled if pref else True
        email_ok = pref.email_enabled if pref else True
        sms_ok = pref.sms_enabled if pref else False

        # If preference is marked mandatory, cannot be disabled
        if pref and pref.is_mandatory:
            in_app_ok = True
            email_ok = True

        created_notification = None
        deliveries = []

        # 1. In-App Notification
        if in_app_ok:
            created_notification = await self.repo.create_notification(
                recipient_id=recipient_id,
                type_=event_type,
                title=title,
                message=message,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                priority=priority,
            )

        # 2. Email Delivery
        if email_ok and recipient_email:
            email_idem_key = f"{idempotency_key_prefix or event_type}:email:{recipient_id}:{recipient_email}"
            # Check if delivery exists
            delivery = await self.repo.create_delivery(
                notification_id=created_notification.id if created_notification else None,
                channel="EMAIL",
                provider="CONSOLE",
                recipient_address=recipient_email,
                idempotency_key=email_idem_key,
                status="PENDING",
            )
            # Dispatch
            res = await self.email_provider.send_email(
                to_address=recipient_email,
                subject=title,
                body_text=message,
            )
            delivery = await self.repo.update_delivery_status(
                delivery_id=delivery.id,
                status=res.status,
                failure_code=res.failure_code,
                error_message=res.error_message,
            )
            if delivery:
                deliveries.append(delivery)

        # 3. SMS Delivery (Requires Explicit SMS Consent)
        if sms_ok and recipient_phone:
            if not sms_consent:
                logger.info("SMS delivery skipped for %s: recipient has not granted explicit SMS consent.", recipient_phone)
            else:
                sms_idem_key = f"{idempotency_key_prefix or event_type}:sms:{recipient_id}:{recipient_phone}"
                delivery = await self.repo.create_delivery(
                    notification_id=created_notification.id if created_notification else None,
                    channel="SMS",
                    provider="CONSOLE",
                    recipient_address=recipient_phone,
                    idempotency_key=sms_idem_key,
                    status="PENDING",
                )
                res = await self.sms_provider.send_sms(
                    to_phone=recipient_phone,
                    body=f"{title}: {message}",
                )
                delivery = await self.repo.update_delivery_status(
                    delivery_id=delivery.id,
                    status=res.status,
                    failure_code=res.failure_code,
                    error_message=res.error_message,
                )
                if delivery:
                    deliveries.append(delivery)

        return {
            "notification": created_notification,
            "deliveries": deliveries,
        }

    async def get_user_notifications(
        self, user_id: uuid.UUID, is_read: bool | None = None, notification_type: str | None = None, page: int = 1, page_size: int = 50
    ) -> tuple[list[Notification], int]:
        return await self.repo.list_user_notifications(user_id, is_read=is_read, notification_type=notification_type, page=page, page_size=page_size)

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        return await self.repo.get_unread_count(user_id)

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
        return await self.repo.mark_as_read(notification_id, user_id)

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        return await self.repo.mark_all_as_read(user_id)

    async def get_user_preferences(self, user_id: uuid.UUID) -> list[NotificationPreference]:
        prefs = await self.repo.get_user_preferences(user_id)
        if not prefs:
            # Seed default preferences for standard categories
            defaults = [
                ("APPOINTMENT_REMINDER", True, True, False, False),
                ("COURT_REMINDER", True, True, False, True),  # Mandatory
                ("GOAL_DUE", True, True, False, False),
                ("LICENSE_EXPIRY", True, True, False, True),  # Mandatory
                ("BACKGROUND_CHECK_EXPIRY", True, True, False, True),  # Mandatory
                ("STAFFING_REMINDER", True, True, False, False),
                ("INTAKE_DECISION", True, True, False, False),
                ("PLAN_REVIEW", True, True, False, False),
                ("CASE_TRANSFER", True, True, False, False),
            ]
            for evt_type, in_app, email, sms, mandatory in defaults:
                p = await self.repo.upsert_preference(
                    user_id=user_id,
                    event_type=evt_type,
                    in_app_enabled=in_app,
                    email_enabled=email,
                    sms_enabled=sms,
                    is_mandatory=mandatory,
                )
                prefs.append(p)
        return prefs

    async def update_user_preference(
        self, user_id: uuid.UUID, event_type: str, in_app_enabled: bool | None, email_enabled: bool | None, sms_enabled: bool | None
    ) -> NotificationPreference:
        return await self.repo.upsert_preference(
            user_id=user_id,
            event_type=event_type,
            in_app_enabled=in_app_enabled,
            email_enabled=email_enabled,
            sms_enabled=sms_enabled,
        )

    async def retry_delivery(self, delivery_id: uuid.UUID) -> NotificationDelivery | None:
        """Retry a failed or retrying delivery record."""
        delivery = await self.repo.get_delivery_by_id(delivery_id)
        if not delivery:
            return None

        if delivery.channel == "EMAIL":
            res = await self.email_provider.send_email(
                to_address=delivery.recipient_address,
                subject="CRBCL Notification Update",
                body_text="You have a pending notification on CRBCL.",
            )
        elif delivery.channel == "SMS":
            res = await self.sms_provider.send_sms(
                to_phone=delivery.recipient_address,
                body="You have a pending notification on CRBCL.",
            )
        else:
            res = None

        if res:
            delivery = await self.repo.update_delivery_status(
                delivery_id=delivery.id,
                status=res.status,
                failure_code=res.failure_code,
                error_message=res.error_message,
            )

        return delivery
