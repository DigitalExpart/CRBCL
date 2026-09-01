"""Calendar events and recurrence rules models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class CalendarEvent(Base, AuditMixin, SoftDeleteMixin):
    """Unified calendar representation across appointments, court hearings, visitations, staffings, and follow-ups."""

    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="APPOINTMENT"
    )  # APPOINTMENT, COURT, VISITATION, CASE_NOTE_FOLLOWUP, STAFFING, ASSESSMENT, PLAN_MEETING, HOME_VISIT, OTHER
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Regina", nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source Entity Linkage (polymorphic reference)
    source_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Scoping & Assignments
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(50), default="SCHEDULED", nullable=False
    )  # SCHEDULED, COMPLETED, CANCELLED, RESCHEDULED, NO_SHOW

    # Relationships
    case = relationship("Case", foreign_keys=[case_id], lazy="selectin")
    person = relationship("Person", foreign_keys=[person_id], lazy="selectin")
    team = relationship("Team", foreign_keys=[team_id], lazy="selectin")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="selectin")
    recurrence_rule = relationship("CalendarRecurrenceRule", back_populates="calendar_event", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="ck_calendar_events_end_after_start"),
        Index("ix_calendar_events_start_end", "start_at", "end_at"),
        Index("ix_calendar_events_source", "source_entity_type", "source_entity_id"),
        Index("ix_calendar_events_event_type", "event_type"),
    )


class CalendarRecurrenceRule(Base):
    """Bounded recurrence parameters for repetitive appointments, visitation, and staffing sessions."""

    __tablename__ = "calendar_recurrence_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    frequency: Mapped[str] = mapped_column(String(20), default="WEEKLY", nullable=False)  # DAILY, WEEKLY, BIWEEKLY, MONTHLY
    interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    by_weekday: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Comma-separated: "MO,WE,FR"
    until_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    max_occurrences: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    calendar_event = relationship("CalendarEvent", back_populates="recurrence_rule")
