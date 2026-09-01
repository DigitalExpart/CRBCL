"""Scheduled reminder and compliance notification engine with deterministic idempotency."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.calendar import CalendarEvent
from app.models.person import Person
from app.models.placement import BackgroundCheck, CourtEvent
from app.models.placement_home import PlacementHomeLicense
from app.models.plan import Plan, PlanActivity, PlanGoal
from app.models.staffing import StaffingAttendee, StaffingSession
from app.models.user import User
from app.services.notification_service import NotificationService

logger = logging.getLogger("crbcl.reminders")


class ScheduledReminderService:
    """Automated scheduled jobs generating idempotent reminders and compliance alerts."""

    def __init__(self, db: AsyncSession, notification_service: NotificationService | None = None):
        self.db = db
        self.notification_service = notification_service or NotificationService(db)

    async def run_all_reminder_jobs(self) -> dict[str, int]:
        """Execute all reminder checks and return counts of generated notifications."""
        results = {
            "appointment_reminders": await self.process_appointment_reminders(),
            "court_reminders": await self.process_court_reminders(),
            "goal_activity_reminders": await self.process_goal_activity_reminders(),
            "license_expiry_reminders": await self.process_license_expiry_reminders(),
            "background_check_expiry_reminders": await self.process_background_check_expiry_reminders(),
            "staffing_reminders": await self.process_staffing_reminders(),
        }
        logger.info("Completed scheduled reminder jobs run: %s", results)
        return results

    # ── 1. Appointment Reminders (24h & 48h) ─────────────────────

    async def process_appointment_reminders(self) -> int:
        now = datetime.now(UTC)
        win_24h_start = now + timedelta(hours=23)
        win_24h_end = now + timedelta(hours=25)
        win_48h_start = now + timedelta(hours=47)
        win_48h_end = now + timedelta(hours=49)

        # Query scheduled appointments in the 24h and 48h windows
        stmt = (
            select(CalendarEvent)
            .options(
                selectinload(CalendarEvent.assigned_user),
                selectinload(CalendarEvent.person).selectinload(Person.contacts),
            )
            .where(
                CalendarEvent.status == "SCHEDULED",
                CalendarEvent.deleted_at.is_(None),
                or_(
                    and_(CalendarEvent.start_at >= win_24h_start, CalendarEvent.start_at <= win_24h_end),
                    and_(CalendarEvent.start_at >= win_48h_start, CalendarEvent.start_at <= win_48h_end),
                ),
            )
        )
        res = await self.db.execute(stmt)
        events = list(res.scalars().all())
        count = 0

        for evt in events:
            window_tag = "24H" if evt.start_at <= win_24h_end else "48H"
            event_date_str = evt.start_at.strftime("%b %d, %Y at %I:%M %p")

            # 1. Notify assigned staff member
            if evt.assigned_user_id and evt.assigned_user:
                idem_key = f"APPT_{window_tag}:{evt.assigned_user_id}:{evt.id}:{evt.start_at.date()}"
                await self.notification_service.notify_user(
                    recipient_id=evt.assigned_user_id,
                    event_type="APPOINTMENT_REMINDER",
                    title=f"Appointment Reminder ({window_tag})",
                    message=f"Reminder: You have a scheduled appointment '{evt.title}' on {event_date_str}.",
                    related_entity_type="calendar_event",
                    related_entity_id=evt.id,
                    recipient_email=evt.assigned_user.email,
                    recipient_phone=evt.assigned_user.phone,
                    idempotency_key_prefix=idem_key,
                    sms_consent=True,
                )
                count += 1

            # 2. Check client consent and dispatch if Person is linked
            if evt.person:
                for contact in evt.person.contacts:
                    if contact.contact_type == "Phone" and contact.sms_consent and contact.value:
                        # Client SMS Reminder (Privacy-safe)
                        client_idem = f"APPT_CLIENT_{window_tag}:{evt.person.id}:{evt.id}:{evt.start_at.date()}"
                        # Note: Notification record recipient is assigned user, external delivery to client phone
                        if evt.assigned_user_id:
                            await self.notification_service.notify_user(
                                recipient_id=evt.assigned_user_id,
                                event_type="APPOINTMENT_REMINDER",
                                title="Client Appointment Reminder",
                                message=f"Reminder: You have an appointment with Chief Red Bear Children's Lodge on {event_date_str}. Contact CRBCL if you need assistance.",
                                related_entity_type="calendar_event",
                                related_entity_id=evt.id,
                                recipient_phone=contact.value,
                                idempotency_key_prefix=client_idem,
                                sms_consent=True,
                            )
                            count += 1

        return count

    # ── 2. Court Reminders (7d & 1d) ─────────────────────────────

    async def process_court_reminders(self) -> int:
        now = datetime.now(UTC)
        target_7d = (now + timedelta(days=7)).date()
        target_1d = (now + timedelta(days=1)).date()

        stmt = (
            select(CourtEvent)
            .options(
                selectinload(CourtEvent.case),
            )
            .where(
                CourtEvent.status == "SCHEDULED",
                CourtEvent.deleted_at.is_(None),
                CourtEvent.hearing_date.in_([target_7d, target_1d]),
            )
        )
        res = await self.db.execute(stmt)
        court_events = list(res.scalars().all())
        count = 0

        for ce in court_events:
            window_tag = "7D" if ce.hearing_date == target_7d else "1D"
            if ce.case and ce.case.assigned_worker_id:
                worker_res = await self.db.execute(select(User).where(User.id == ce.case.assigned_worker_id))
                worker = worker_res.scalar_one_or_none()
                if worker:
                    idem_key = f"COURT_{window_tag}:{worker.id}:{ce.id}:{ce.hearing_date}"

                    hearing_type_name = ce.hearing_type.replace("_", " ").title()
                    await self.notification_service.notify_user(
                        recipient_id=worker.id,
                        event_type="COURT_REMINDER",
                        title=f"Court Hearing Upcoming ({window_tag})",
                        message=f"Upcoming {hearing_type_name} scheduled for case {ce.case.case_number} on {ce.hearing_date} at {ce.court_location or 'Court'}.",
                        related_entity_type="court_event",
                        related_entity_id=ce.id,
                        priority="HIGH" if window_tag == "1D" else "NORMAL",
                        recipient_email=worker.email,
                        recipient_phone=worker.phone,
                        idempotency_key_prefix=idem_key,
                        sms_consent=True,
                    )
                    count += 1

        return count

    # ── 3. Plan Goal & Activity Reminders ────────────────────────

    async def process_goal_activity_reminders(self) -> int:
        now = datetime.now(UTC).date()
        due_soon_threshold = now + timedelta(days=3)

        from app.models.plan import PlanVersion

        # 1. Activities
        stmt = (
            select(PlanActivity)
            .join(PlanGoal, PlanActivity.goal_id == PlanGoal.id)
            .join(PlanVersion, PlanGoal.plan_version_id == PlanVersion.id)
            .join(Plan, PlanVersion.plan_id == Plan.id)
            .options(
                selectinload(PlanActivity.goal)
                .selectinload(PlanGoal.plan_version)
                .selectinload(PlanVersion.plan)
                .selectinload(Plan.case),
            )
            .where(
                PlanActivity.status.in_(["NOT_STARTED", "IN_PROGRESS"]),
                PlanActivity.due_date <= due_soon_threshold,
                Plan.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        activities = list(res.scalars().all())
        count = 0

        for act in activities:
            is_overdue = act.due_date and act.due_date < now
            tag = "OVERDUE" if is_overdue else "DUE_SOON"

            plan = act.goal.plan_version.plan if act.goal and act.goal.plan_version else None
            worker_id = plan.case.assigned_worker_id if plan and plan.case else None
            if worker_id:
                worker_res = await self.db.execute(select(User).where(User.id == worker_id))
                worker = worker_res.scalar_one_or_none()
                if worker:
                    idem_key = f"PLAN_ACT_{tag}:{worker.id}:{act.id}:{act.due_date}:{now}"
                    await self.notification_service.notify_user(
                        recipient_id=worker.id,
                        event_type="GOAL_DUE",
                        title=f"Plan Activity {tag.replace('_', ' ').title()}",
                        message=f"Plan activity '{act.activity_text}' is {tag.lower().replace('_', ' ')} (Due: {act.due_date}).",
                        related_entity_type="plan_activity",
                        related_entity_id=act.id,
                        priority="HIGH" if is_overdue else "NORMAL",
                        recipient_email=worker.email,
                        idempotency_key_prefix=idem_key,
                    )
                    count += 1

        return count

    # ── 4. Placement Home License Expiry Alerts ──────────────────

    async def process_license_expiry_reminders(self) -> int:
        now = datetime.now(UTC).date()
        threshold_60 = now + timedelta(days=60)

        stmt = (
            select(PlacementHomeLicense)
            .options(selectinload(PlacementHomeLicense.placement_home))
            .where(
                PlacementHomeLicense.status == "ACTIVE",
                PlacementHomeLicense.expiry_date.isnot(None),
                PlacementHomeLicense.expiry_date <= threshold_60,
                PlacementHomeLicense.expiry_date >= now,
            )
        )
        res = await self.db.execute(stmt)
        licenses = list(res.scalars().all())
        count = 0

        # Query admin users
        admin_stmt = select(User).where(User.is_active == True, User.deleted_at.is_(None))  # noqa: E712
        admin_res = await self.db.execute(admin_stmt)
        admins = list(admin_res.scalars().all())

        for lic in licenses:
            days_left = (lic.expiry_date - now).days
            window_tag = "15D" if days_left <= 15 else ("30D" if days_left <= 30 else "60D")

            home_name = lic.placement_home.name if lic.placement_home else "Placement Home"
            for admin in admins[:3]:  # Alert lead admin staff
                idem_key = f"LIC_EXPIRY_{window_tag}:{admin.id}:{lic.id}:{lic.expiry_date}"
                await self.notification_service.notify_user(
                    recipient_id=admin.id,
                    event_type="LICENSE_EXPIRY",
                    title="Placement Home License Expiring Soon",
                    message=f"License for '{home_name}' expires in {days_left} days ({lic.expiry_date}). Review required.",
                    related_entity_type="placement_home_license",
                    related_entity_id=lic.id,
                    priority="HIGH" if days_left <= 15 else "NORMAL",
                    recipient_email=admin.email,
                    idempotency_key_prefix=idem_key,
                )
                count += 1

        return count

    # ── 5. Background Check Expiry Alerts ────────────────────────

    async def process_background_check_expiry_reminders(self) -> int:
        now = datetime.now(UTC).date()
        threshold_30 = now + timedelta(days=30)

        stmt = select(BackgroundCheck).where(
            BackgroundCheck.status == "PASSED",
            BackgroundCheck.expiry_date.isnot(None),
            BackgroundCheck.expiry_date <= threshold_30,
            BackgroundCheck.expiry_date >= now,
            BackgroundCheck.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        checks = list(res.scalars().all())
        count = 0

        admin_stmt = select(User).where(User.is_active == True, User.deleted_at.is_(None))  # noqa: E712
        admin_res = await self.db.execute(admin_stmt)
        admins = list(admin_res.scalars().all())

        for bc in checks:
            days_left = (bc.expiry_date - now).days
            for admin in admins[:2]:
                idem_key = f"BG_EXPIRY:{admin.id}:{bc.id}:{bc.expiry_date}"
                await self.notification_service.notify_user(
                    recipient_id=admin.id,
                    event_type="BACKGROUND_CHECK_EXPIRY",
                    title="Background Check Expiring",
                    message=f"Background check for {bc.subject_name} ({bc.check_type}) expires in {days_left} days.",
                    related_entity_type="background_check",
                    related_entity_id=bc.id,
                    recipient_email=admin.email,
                    idempotency_key_prefix=idem_key,
                )
                count += 1

        return count

    # ── 6. Staffing Session Reminders (24h) ──────────────────────

    async def process_staffing_reminders(self) -> int:
        now = datetime.now(UTC)
        win_24h_start = now + timedelta(hours=23)
        win_24h_end = now + timedelta(hours=25)

        stmt = (
            select(StaffingSession)
            .options(
                selectinload(StaffingSession.facilitator),
                selectinload(StaffingSession.attendees).selectinload(StaffingAttendee.user),
            )
            .where(
                StaffingSession.status == "SCHEDULED",
                StaffingSession.deleted_at.is_(None),
                StaffingSession.session_date >= win_24h_start,
                StaffingSession.session_date <= win_24h_end,
            )
        )
        res = await self.db.execute(stmt)
        sessions = list(res.scalars().all())
        count = 0

        for s in sessions:
            date_str = s.session_date.strftime("%b %d, %Y at %I:%M %p")

            recipients = []
            if s.facilitator:
                recipients.append(s.facilitator)
            for a in s.attendees:
                if a.user and a.user not in recipients:
                    recipients.append(a.user)

            for user in recipients:
                idem_key = f"STAFFING_24H:{user.id}:{s.id}:{s.session_date.date()}"
                await self.notification_service.notify_user(
                    recipient_id=user.id,
                    event_type="STAFFING_REMINDER",
                    title="Staffing Session Reminder (24h)",
                    message=f"Reminder: You are scheduled to attend the staffing session '{s.title}' on {date_str}.",
                    related_entity_type="staffing_session",
                    related_entity_id=s.id,
                    recipient_email=user.email,
                    idempotency_key_prefix=idem_key,
                )
                count += 1

        return count
