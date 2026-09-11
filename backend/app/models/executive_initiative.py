"""Executive Organizational Initiatives domain models for CRBCL CEO Dashboard."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.board_action import BoardAction
    from app.models.user import User


class ExecutiveInitiative(Base, AuditMixin, SoftDeleteMixin):
    """Strategic organizational initiative or major deliverable."""

    __tablename__ = "executive_initiatives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    department: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    responsible_owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ON_TRACK", index=True
    )  # ON_TRACK, AT_RISK, DELAYED, ON_HOLD, COMPLETED, CANCELLED
    priority: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MEDIUM", index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL

    target_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latest_update: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporting_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Board publication boundary
    is_board_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    board_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_for_board_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_for_board_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    responsible_owner: Mapped[User | None] = relationship("User", foreign_keys=[responsible_owner_id], lazy="selectin")
    approved_for_board_by: Mapped[User | None] = relationship("User", foreign_keys=[approved_for_board_by_id], lazy="selectin")
    history: Mapped[list[ExecutiveInitiativeHistory]] = relationship(
        "ExecutiveInitiativeHistory",
        back_populates="initiative",
        cascade="all, delete-orphan",
        order_by="desc(ExecutiveInitiativeHistory.changed_at)",
        lazy="selectin",
    )
    board_actions: Mapped[list[BoardAction]] = relationship(
        "BoardAction",
        back_populates="linked_initiative",
        lazy="selectin",
    )


class ExecutiveInitiativeHistory(Base):
    """Append-only audit ledger of initiative progress, status transitions, and reporting notes."""

    __tablename__ = "executive_initiative_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    initiative_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executive_initiatives.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    progress_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    update_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False, index=True
    )

    initiative: Mapped[ExecutiveInitiative] = relationship("ExecutiveInitiative", back_populates="history")
    changed_by: Mapped[User | None] = relationship("User", foreign_keys=[changed_by_id], lazy="selectin")
