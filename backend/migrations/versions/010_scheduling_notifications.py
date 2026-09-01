"""010 — Unified Scheduling, Team Calendar, Staffing Facilitator, Notifications, Reminders, and Deliveries.

Revision ID: 010_scheduling_notifications
Revises: 009_placement_homes
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_scheduling_notifications"
down_revision: str | None = "009_placement_homes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Create calendar_events table ─────────────────────────
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(length=50), nullable=False, server_default="APPOINTMENT"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="America/Regina"),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_entity_type", sa.String(length=50), nullable=True),
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SCHEDULED"),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("end_at >= start_at", name="ck_calendar_events_end_after_start"),
    )
    op.create_index("ix_calendar_events_start_end", "calendar_events", ["start_at", "end_at"])
    op.create_index("ix_calendar_events_assigned_user", "calendar_events", ["assigned_user_id"])
    op.create_index("ix_calendar_events_team", "calendar_events", ["team_id"])
    op.create_index("ix_calendar_events_case", "calendar_events", ["case_id"])
    op.create_index("ix_calendar_events_source", "calendar_events", ["source_entity_type", "source_entity_id"])
    op.create_index("ix_calendar_events_event_type", "calendar_events", ["event_type"])

    # ── 2. Create calendar_recurrence_rules table ───────────────
    op.create_table(
        "calendar_recurrence_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("calendar_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="WEEKLY"),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("by_weekday", sa.String(length=50), nullable=True),
        sa.Column("until_date", sa.Date(), nullable=True),
        sa.Column("max_occurrences", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ── 3. Create staffing_sessions table ───────────────────────
    op.create_table(
        "staffing_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("facilitator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cadence", sa.String(length=50), nullable=False, server_default="WEEKLY"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SCHEDULED"),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("minutes", sa.Text(), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_staffing_sessions_date", "staffing_sessions", ["session_date"])
    op.create_index("ix_staffing_sessions_team", "staffing_sessions", ["team_id"])
    op.create_index("ix_staffing_sessions_status", "staffing_sessions", ["status"])

    # ── 4. Create staffing_attendees table ──────────────────────
    op.create_table(
        "staffing_attendees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staffing_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attendance_status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "user_id", name="uq_staffing_attendee_session_user"),
    )
    op.create_index("ix_staffing_attendees_session", "staffing_attendees", ["session_id"])
    op.create_index("ix_staffing_attendees_user", "staffing_attendees", ["user_id"])

    # ── 5. Create staffing_cases table ──────────────────────────
    op.create_table(
        "staffing_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staffing_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("review_status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("discussion_summary", sa.Text(), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("assigned_worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "case_id", name="uq_staffing_case_session_case"),
    )
    op.create_index("ix_staffing_cases_session", "staffing_cases", ["session_id"])
    op.create_index("ix_staffing_cases_case", "staffing_cases", ["case_id"])
    op.create_index("ix_staffing_cases_review_status", "staffing_cases", ["review_status"])

    # ── 6. Create notifications table ───────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_entity_type", sa.String(length=50), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="NORMAL"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_recipient_read", "notifications", ["recipient_id", "is_read"])
    op.create_index("ix_notifications_recipient_created", "notifications", ["recipient_id", "created_at"])
    op.create_index("ix_notifications_type", "notifications", ["type"])

    # ── 7. Create notification_preferences table ────────────────
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "event_type", name="uq_notification_pref_user_event"),
    )
    op.create_index("ix_notification_preferences_user", "notification_preferences", ["user_id"])

    # ── 8. Create notification_deliveries table ──────────────────
    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=True),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="CONSOLE"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("recipient_address", sa.String(length=320), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_notification_deliveries_status_created", "notification_deliveries", ["status", "created_at"])
    op.create_index("ix_notification_deliveries_idempotency", "notification_deliveries", ["idempotency_key"])

    # ── 9. Create notification_templates table ──────────────────
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("title_template", sa.String(length=255), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("event_type", "channel", name="uq_notification_template_type_channel"),
    )

    # ── 10. Add contact consent columns to person_contacts ──────
    op.add_column("person_contacts", sa.Column("sms_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("person_contacts", sa.Column("email_consent", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("person_contacts", sa.Column("preferred_contact_method", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("person_contacts", "preferred_contact_method")
    op.drop_column("person_contacts", "email_consent")
    op.drop_column("person_contacts", "sms_consent")
    op.drop_table("notification_templates")
    op.drop_table("notification_deliveries")
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
    op.drop_table("staffing_cases")
    op.drop_table("staffing_attendees")
    op.drop_table("staffing_sessions")
    op.drop_table("calendar_recurrence_rules")
    op.drop_table("calendar_events")
