"""Department Executive Update model for periodic CEO reporting."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.board_action import BoardAction
    from app.models.executive_initiative import ExecutiveInitiative
    from app.models.user import User


class DepartmentExecutiveUpdate(Base, AuditMixin, SoftDeleteMixin):
    """Periodic executive update submitted by department leadership for CEO review."""

    __tablename__ = "department_executive_updates"
    __table_args__ = (
        UniqueConstraint(
            "reporting_period", "department", "deleted_at",
            name="uq_dept_exec_update_period_department"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporting_period: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. "2026-04", "2026-Q1"
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    submitted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=True
    )

    headline_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    accomplishments_narrative: Mapped[str] = mapped_column(Text, nullable=False, default="")
    risks_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_decision_requested: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SUBMITTED", index=True
    )  # DRAFT, SUBMITTED, ACKNOWLEDGED

    linked_initiative_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executive_initiatives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    linked_board_action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("board_actions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Board publication boundary
    is_board_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    approved_for_board_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_for_board_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    submitted_by: Mapped[User | None] = relationship("User", foreign_keys=[submitted_by_id], lazy="selectin")
    approved_for_board_by: Mapped[User | None] = relationship("User", foreign_keys=[approved_for_board_by_id], lazy="selectin")
    linked_initiative: Mapped[ExecutiveInitiative | None] = relationship("ExecutiveInitiative", lazy="selectin")
    linked_board_action: Mapped[BoardAction | None] = relationship("BoardAction", lazy="selectin")

    history: Mapped[list[DepartmentExecutiveUpdateHistory]] = relationship(
        "DepartmentExecutiveUpdateHistory",
        back_populates="update",
        cascade="all, delete-orphan",
        order_by="desc(DepartmentExecutiveUpdateHistory.changed_at)",
        lazy="selectin",
    )


class DepartmentExecutiveUpdateHistory(Base):
    """Append-only snapshot of each prior version of a DepartmentExecutiveUpdate narrative.

    Written immediately before any overwrite so the full revision history is preserved.
    """

    __tablename__ = "department_executive_update_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    update_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("department_executive_updates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reporting_period: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_headline_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    previous_accomplishments_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_risks_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False, index=True
    )

    update: Mapped[DepartmentExecutiveUpdate] = relationship("DepartmentExecutiveUpdate", back_populates="history")
    changed_by: Mapped[User | None] = relationship("User", foreign_keys=[changed_by_id], lazy="selectin")
