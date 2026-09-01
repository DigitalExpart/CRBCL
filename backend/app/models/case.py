"""Case model with Phase 4 extensions and relationships."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class Case(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    case_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Open", nullable=False)
    stage: Mapped[str] = mapped_column(String(50), default="INVESTIGATION", nullable=False)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    intake_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_resolution_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reopened_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase 14 Legal Hold / Retention Governance
    is_legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    legal_hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_hold_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    legal_hold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Legacy & primary convenience references
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    family_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_worker_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    assigned_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Provenance from Phase 3 Intake
    origin_referral_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="SET NULL", use_alter=True), nullable=True, index=True
    )
    origin_disposition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child_dispositions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
        index=True,
    )

    # Relational Sub-entities
    people = relationship("CasePerson", back_populates="case", cascade="all, delete-orphan")
    assignments = relationship("CaseAssignment", back_populates="case", cascade="all, delete-orphan")
    external_workers = relationship("CaseExternalWorker", back_populates="case", cascade="all, delete-orphan")
    sources = relationship("CaseSource", back_populates="case", cascade="all, delete-orphan")
    outgoing_links = relationship(
        "CaseLink", foreign_keys="CaseLink.source_case_id", back_populates="source_case", cascade="all, delete-orphan"
    )
    incoming_links = relationship(
        "CaseLink", foreign_keys="CaseLink.target_case_id", back_populates="target_case", cascade="all, delete-orphan"
    )
    restrictions = relationship("CaseRestriction", back_populates="case", cascade="all, delete-orphan")
    transfers = relationship("CaseTransfer", back_populates="case", cascade="all, delete-orphan")
    status_history = relationship("CaseStatusHistory", back_populates="case", cascade="all, delete-orphan")
    case_notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_priority", "priority"),
        Index("ix_cases_stage", "stage"),
        Index("ix_cases_case_type", "case_type"),
        Index("ix_cases_origin_referral", "origin_referral_id"),
    )
