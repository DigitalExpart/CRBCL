"""Notification repository for in-app alerts, preferences, delivery tracking, and templates."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
    NotificationTemplate,
)


class NotificationRepo:
    """Data access layer for notifications, preferences, outbox deliveries, and templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        recipient_id: uuid.UUID,
        type_: str,
        title: str,
        message: str,
        related_entity_type: str | None = None,
        related_entity_id: uuid.UUID | None = None,
        priority: str = "NORMAL",
    ) -> Notification:
        notification = Notification(
            recipient_id=recipient_id,
            type=type_,
            title=title,
            message=message,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            priority=priority,
            is_read=False,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        stmt = (
            select(Notification)
            .where(Notification.id == notification_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_notifications(
        self,
        user_id: uuid.UUID,
        is_read: bool | None = None,
        notification_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Notification], int]:
        conditions = [Notification.recipient_id == user_id]
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)
        if notification_type:
            conditions.append(Notification.type == notification_type)

        count_stmt = select(func.count(Notification.id)).where(and_(*conditions))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.recipient_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == user_id,
        )
        res = await self.db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self.db.flush()

        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.recipient_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(
                is_read=True,
                read_at=datetime.now(UTC),
            )
        )
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount

    # ── Preferences ─────────────────────────────────────────────

    async def get_user_preferences(self, user_id: uuid.UUID) -> list[NotificationPreference]:
        stmt = (
            select(NotificationPreference)
            .where(NotificationPreference.user_id == user_id)
            .order_by(NotificationPreference.event_type.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_preference_for_event(self, user_id: uuid.UUID, event_type: str) -> NotificationPreference | None:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.event_type == event_type,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def upsert_preference(
        self,
        user_id: uuid.UUID,
        event_type: str,
        in_app_enabled: bool | None = None,
        email_enabled: bool | None = None,
        sms_enabled: bool | None = None,
        is_mandatory: bool = False,
    ) -> NotificationPreference:
        pref = await self.get_preference_for_event(user_id, event_type)
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                event_type=event_type,
                in_app_enabled=in_app_enabled if in_app_enabled is not None else True,
                email_enabled=email_enabled if email_enabled is not None else True,
                sms_enabled=sms_enabled if sms_enabled is not None else False,
                is_mandatory=is_mandatory,
            )
            self.db.add(pref)
        else:
            # If preference is mandatory compliance, email and in-app cannot be disabled!
            if not pref.is_mandatory:
                if in_app_enabled is not None:
                    pref.in_app_enabled = in_app_enabled
                if email_enabled is not None:
                    pref.email_enabled = email_enabled
                if sms_enabled is not None:
                    pref.sms_enabled = sms_enabled
            else:
                if sms_enabled is not None:
                    pref.sms_enabled = sms_enabled

            pref.updated_at = datetime.now(UTC)

        await self.db.flush()
        return pref

    # ── Deliveries ──────────────────────────────────────────────

    async def create_delivery(
        self,
        notification_id: uuid.UUID | None,
        channel: str,
        provider: str,
        recipient_address: str,
        idempotency_key: str,
        status: str = "PENDING",
        failure_code: str | None = None,
        error_message: str | None = None,
    ) -> NotificationDelivery:
        # Check for existing idempotency key
        existing = await self.get_delivery_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        delivery = NotificationDelivery(
            notification_id=notification_id,
            channel=channel,
            provider=provider,
            status=status,
            recipient_address=recipient_address,
            idempotency_key=idempotency_key,
            failure_code=failure_code,
            error_message=error_message,
        )
        self.db.add(delivery)
        await self.db.flush()
        return delivery

    async def get_delivery_by_idempotency_key(self, idempotency_key: str) -> NotificationDelivery | None:
        stmt = select(NotificationDelivery).where(NotificationDelivery.idempotency_key == idempotency_key)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_delivery_by_id(self, delivery_id: uuid.UUID) -> NotificationDelivery | None:
        stmt = select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_deliveries(
        self, status: str | None = None, channel: str | None = None, page: int = 1, page_size: int = 50
    ) -> tuple[list[NotificationDelivery], int]:
        conditions = []
        if status:
            conditions.append(NotificationDelivery.status == status)
        if channel:
            conditions.append(NotificationDelivery.channel == channel)

        count_stmt = select(func.count(NotificationDelivery.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = select(NotificationDelivery)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = (
            stmt.order_by(NotificationDelivery.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def update_delivery_status(
        self,
        delivery_id: uuid.UUID,
        status: str,
        failure_code: str | None = None,
        error_message: str | None = None,
    ) -> NotificationDelivery | None:
        delivery = await self.get_delivery_by_id(delivery_id)
        if not delivery:
            return None

        delivery.status = status
        delivery.last_attempt_at = datetime.now(UTC)
        delivery.attempt_count += 1

        if status == "SENT":
            delivery.sent_at = datetime.now(UTC)
            delivery.failure_code = None
            delivery.error_message = None
        elif status in ("FAILED", "RETRYING"):
            delivery.failed_at = datetime.now(UTC)
            delivery.failure_code = failure_code
            delivery.error_message = error_message

        await self.db.flush()
        return delivery

    # ── Templates ───────────────────────────────────────────────

    async def get_template(self, event_type: str, channel: str) -> NotificationTemplate | None:
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.event_type == event_type,
            NotificationTemplate.channel == channel,
            NotificationTemplate.is_active == True,  # noqa: E712
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_templates(self) -> list[NotificationTemplate]:
        stmt = select(NotificationTemplate).order_by(NotificationTemplate.event_type.asc(), NotificationTemplate.channel.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def upsert_template(
        self, event_type: str, channel: str, title_template: str, body_template: str, is_active: bool = True
    ) -> NotificationTemplate:
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.event_type == event_type,
            NotificationTemplate.channel == channel,
        )
        res = await self.db.execute(stmt)
        template = res.scalar_one_or_none()
        if not template:
            template = NotificationTemplate(
                event_type=event_type,
                channel=channel,
                title_template=title_template,
                body_template=body_template,
                is_active=is_active,
            )
            self.db.add(template)
        else:
            template.title_template = title_template
            template.body_template = body_template
            template.is_active = is_active
            template.updated_at = datetime.now(UTC)

        await self.db.flush()
        return template
