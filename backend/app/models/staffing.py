"""Staffing sessions, attendees, and case review models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class StaffingSession(Base, AuditMixin, SoftDeleteMixin):
    """Multi-disciplinary case review and staffing conference session."""

    __tablename__ = "staffing_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    facilitator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cadence: Mapped[str] = mapped_column(
        String(50), default="WEEKLY", nullable=False
    )  # WEEKLY, BIWEEKLY, MONTHLY, AD_HOC
    status: Mapped[str] = mapped_column(
        String(50), default="SCHEDULED", nullable=False
    )  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minutes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    facilitator = relationship("User", foreign_keys=[facilitator_id], lazy="selectin")
    team = relationship("Team", foreign_keys=[team_id], lazy="selectin")
    attendees = relationship(
        "StaffingAttendee", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
    cases = relationship("StaffingCase", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("ix_staffing_sessions_date", "session_date"),
        Index("ix_staffing_sessions_status", "status"),
    )


class StaffingAttendee(Base):
    """Staff member or collateral participating in a staffing session."""

    __tablename__ = "staffing_attendees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staffing_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attendance_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )  # ATTENDED, ABSENT, EXCUSED, PENDING
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    session = relationship("StaffingSession", back_populates="attendees")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")

    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uq_staffing_attendee_session_user"),)


class StaffingCase(Base):
    """Specific case scheduled for review during a staffing session."""

    __tablename__ = "staffing_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staffing_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )  # PENDING, REVIEWED, DEFERRED, ESCALATED
    discussion_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    session = relationship("StaffingSession", back_populates="cases")
    case = relationship("Case", foreign_keys=[case_id], lazy="selectin")
    assigned_worker = relationship("User", foreign_keys=[assigned_worker_id], lazy="selectin")

    __table_args__ = (UniqueConstraint("session_id", "case_id", name="uq_staffing_case_session_case"),)
