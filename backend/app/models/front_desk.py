"""Front Desk and Public Intake Ingestion domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.referral import Referral
    from app.models.user import User


class FrontDeskSequence(Base):
    """Atomic counter for concurrency-safe human-readable front desk submission numbers (e.g. FD-2026-000001)."""

    __tablename__ = "front_desk_sequences"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class FrontDeskSubmission(Base, AuditMixin, SoftDeleteMixin):
    """Front Desk Public Intake & Ingestion Submission entity."""

    __tablename__ = "front_desk_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    external_response_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    source: Mapped[str] = mapped_column(String(50), default="google_form", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", nullable=False, index=True)

    urgency: Mapped[str] = mapped_column(String(50), default="Medium", nullable=False)
    destination_department: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    destination_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )

    submitter_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    submitter_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    submitter_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    submitter_relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)

    inquiry_type: Mapped[str] = mapped_column(String(100), default="general_inquiry", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )

    front_desk_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    front_desk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    department_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    department_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    resulting_referral_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    front_desk_worker: Mapped[User | None] = relationship(
        "User", foreign_keys=[front_desk_worker_id], lazy="selectin"
    )
    department_worker: Mapped[User | None] = relationship(
        "User", foreign_keys=[department_worker_id], lazy="selectin"
    )
    resulting_referral: Mapped[Referral | None] = relationship(
        "Referral", foreign_keys=[resulting_referral_id], lazy="selectin"
    )
    routing_history: Mapped[list[FrontDeskRoutingHistory]] = relationship(
        "FrontDeskRoutingHistory",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="FrontDeskRoutingHistory.changed_at",
        lazy="selectin",
    )
    conversion_links: Mapped[list[PublicIntakeConversionLink]] = relationship(
        "PublicIntakeConversionLink",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="PublicIntakeConversionLink.created_at",
        lazy="selectin",
    )


class FrontDeskRoutingHistory(Base):
    """Append-only audit ledger of every routing transition."""

    __tablename__ = "front_desk_routing_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("front_desk_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_destination: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_destination: Mapped[str | None] = mapped_column(String(100), nullable=True)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )
    reason_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission: Mapped[FrontDeskSubmission] = relationship(
        "FrontDeskSubmission", back_populates="routing_history"
    )
    changed_by: Mapped[User | None] = relationship("User", lazy="selectin")


class PublicIntakeConversionLink(Base):
    """Generic linkage record connecting a Public Intake Submission to any downstream domain record."""

    __tablename__ = "public_intake_conversion_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("front_desk_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    downstream_entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    downstream_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    downstream_entity_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission: Mapped[FrontDeskSubmission] = relationship(
        "FrontDeskSubmission", back_populates="conversion_links"
    )
    created_by: Mapped[User | None] = relationship("User", lazy="selectin")
