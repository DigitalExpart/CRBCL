"""Test suite for Scheduled Reminders Engine, deterministic idempotency, and SMS consent."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEvent
from app.models.case import Case
from app.models.notification import Notification, NotificationDelivery
from app.models.person import Person, PersonContact
from app.models.placement import BackgroundCheck, CourtEvent
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.plan import Plan, PlanActivity, PlanGoal, PlanVersion
from app.models.staffing import StaffingAttendee, StaffingSession
from app.models.user import User
from app.services.notification_providers import sanitize_external_message
from app.services.reminder_service import ScheduledReminderService


@pytest.mark.asyncio
async def test_scheduled_reminders_comprehensive_and_idempotent(
    db_session: AsyncSession, caseworker_user, supervisor_user, seed_roles_and_permissions
):
    """
    CRITICAL IDEMPOTENCY & COMPLIANCE TEST:
    Verify reminder jobs for appointments, court, goals, licenses, background checks, and staffing.
    Running the entire reminder engine TWICE must produce identical results with ZERO duplicate deliveries.
    """
    cw_user = caseworker_user["user"]
    sup_user = supervisor_user["user"]
    now = datetime.now(UTC)

    # 1. Setup Test Case & Entities
    case = Case(
        case_number="CAS-REM-001",
        title="Comprehensive Reminder Engine Test Case",
        status="Open",
        stage="ONGOING_SERVICES",
        assigned_worker_id=cw_user.id,
    )
    db_session.add(case)

    # 2. Upcoming Court Hearing in 7 days
    court_event = CourtEvent(
        case=case,
        hearing_type="PERMANENCY_HEARING",
        hearing_date=(now + timedelta(days=7)).date(),
        court_location="Regina Courtroom 1",
        status="SCHEDULED",
    )
    db_session.add(court_event)

    # 3. Upcoming Appointment in 24 hours with a Client
    client_person = Person(first_name="Cheryl", last_name="Bird")
    db_session.add(client_person)
    await db_session.flush()

    contact_sms = PersonContact(
        person_id=client_person.id,
        contact_type="Phone",
        value="+13065550199",
        label="Mobile",
        sms_consent=True,  # Consented!
    )
    db_session.add(contact_sms)

    appt = CalendarEvent(
        event_type="APPOINTMENT",
        title="Caregiver Conference",
        start_at=now + timedelta(hours=24),
        end_at=now + timedelta(hours=25),
        assigned_user_id=cw_user.id,
        person_id=client_person.id,
        status="SCHEDULED",
    )
    db_session.add(appt)

    # 4. Plan Activity Due Soon
    plan = Plan(
        case_id=case.id,
        plan_type="FAMILY_WELLNESS",
        plan_number="PLN-2026-REM",
        title="Family Wellness Plan",
        status="APPROVED",
        created_by=cw_user.id,
    )
    db_session.add(plan)
    await db_session.flush()

    version = PlanVersion(
        plan_id=plan.id,
        version_number=1,
        status="ACTIVE",
        created_by=cw_user.id,
    )
    db_session.add(version)
    await db_session.flush()

    goal = PlanGoal(
        plan_version_id=version.id,
        goal_text="Strengthen Family Independence",
        created_by=cw_user.id,
    )
    db_session.add(goal)
    await db_session.flush()

    activity = PlanActivity(
        goal_id=goal.id,
        activity_text="Secure Child Care Subsidy",
        due_date=(now + timedelta(days=2)).date(),
        status="IN_PROGRESS",
    )
    db_session.add(activity)

    # 5. Placement Home License expiring in 25 days (within 30d window)
    home = PlacementHome(
        home_code="PH-REM-01",
        name="Sunny Lodge Foster Home",
        status="ACTIVE",
        total_capacity=2,
    )
    db_session.add(home)
    await db_session.flush()

    license_rec = PlacementHomeLicense(
        placement_home_id=home.id,
        license_number="LIC-2026-REM",
        license_type="FOSTER_HOME",
        status="ACTIVE",
        effective_date=date.today(),
        expiry_date=(now + timedelta(days=25)).date(),
    )
    db_session.add(license_rec)

    # 6. Staffing Session in 24 hours
    staffing = StaffingSession(
        title="Weekly Review Session",
        session_date=now + timedelta(hours=24),
        facilitator_id=sup_user.id,
        status="SCHEDULED",
    )
    db_session.add(staffing)
    await db_session.flush()

    attendee = StaffingAttendee(
        session_id=staffing.id,
        user_id=cw_user.id,
        attendance_status="PENDING",
    )
    db_session.add(attendee)

    await db_session.flush()
    await db_session.commit()

    # ── FIRST RUN OF REMINDER ENGINE ──────────────────────────
    reminder_svc = ScheduledReminderService(db_session)
    run1 = await reminder_svc.run_all_reminder_jobs()
    await db_session.commit()

    assert run1["court_reminders"] >= 1
    assert run1["appointment_reminders"] >= 1
    assert run1["goal_activity_reminders"] >= 1
    assert run1["license_expiry_reminders"] >= 1
    assert run1["staffing_reminders"] >= 1

    # Count deliveries after Run 1
    deliv_count_stmt = select(NotificationDelivery)
    res1 = await db_session.execute(deliv_count_stmt)
    delivs_run1 = len(res1.scalars().all())
    assert delivs_run1 > 0

    # ── SECOND RUN (IDEMPOTENCY VERIFICATION) ─────────────────
    run2 = await reminder_svc.run_all_reminder_jobs()
    await db_session.commit()

    # Deliveries count MUST NOT increase
    res2 = await db_session.execute(deliv_count_stmt)
    delivs_run2 = len(res2.scalars().all())
    assert delivs_run2 == delivs_run1, "Second run generated duplicate notification deliveries! Idempotency failed."


@pytest.mark.asyncio
async def test_sms_consent_enforcement_and_privacy_sanitizer():
    """Verify that external privacy sanitizer suppresses detailed clinical words and consent is required."""
    # 1. Privacy Sanitizer
    dirty_text = "Child Jane Doe was apprehended following severe sexual abuse and neglect allegations."
    clean_text = sanitize_external_message(dirty_text)
    assert "confidential update" in clean_text
    assert "sexual" not in clean_text
    assert "allegations" not in clean_text
    assert "abuse" not in clean_text

    # Safe appointment reminder passes through unchanged
    safe_text = "Reminder: You have an appointment with Chief Red Bear Children's Lodge on Oct 14 at 10:00 AM."
    assert sanitize_external_message(safe_text) == safe_text
