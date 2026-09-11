"""Board Action / Governance requests model for CRBCL CEO Dashboard and Board attention."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.executive_initiative import ExecutiveInitiative
    from app.models.user import User


class BoardAction(Base, AuditMixin, SoftDeleteMixin):
    """Governance action or decision requested for Board attention."""

    __tablename__ = "board_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    originating_department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    linked_initiative_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executive_initiatives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    background_summary: Mapped[str] = mapped_column(Text, nullable=False)
    requested_action: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MEDIUM", index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL
    required_by_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SUBMITTED", index=True
    )  # DRAFT, SUBMITTED, UNDER_REVIEW, DECISION_REQUIRED, APPROVED, DECLINED, DEFERRED, RESOLVED, WITHDRAWN

    submitted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Future Board Dashboard boundary: ensure governance readiness
    is_governance_ready: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    linked_initiative: Mapped[ExecutiveInitiative | None] = relationship(
        "ExecutiveInitiative", back_populates="board_actions", lazy="selectin"
    )
    submitted_by: Mapped[User | None] = relationship("User", foreign_keys=[submitted_by_id], lazy="selectin")
    decided_by: Mapped[User | None] = relationship("User", foreign_keys=[decided_by_id], lazy="selectin")

    history: Mapped[list[BoardActionHistory]] = relationship(
        "BoardActionHistory",
        back_populates="board_action",
        cascade="all, delete-orphan",
        order_by="desc(BoardActionHistory.changed_at)",
        lazy="selectin",
    )


class BoardActionHistory(Base):
    """Append-only audit log of status changes and decision resolutions for Board actions."""

    __tablename__ = "board_action_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("board_actions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False, index=True
    )

    board_action: Mapped[BoardAction] = relationship("BoardAction", back_populates="history")
    changed_by: Mapped[User | None] = relationship("User", foreign_keys=[changed_by_id], lazy="selectin")
