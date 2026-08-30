"""Referral, Screening, Decision, and Intake domain models."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class ReferralSequence(Base):
    """Atomic counter for concurrency-safe human-readable referral numbers (e.g. INT-2026-000001)."""
    __tablename__ = "referral_sequences"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Referral(Base, AuditMixin, SoftDeleteMixin):
    """Primary Referral / Intake domain entity."""
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False, index=True)
    
    received_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_method: Mapped[str] = mapped_column(String(50), default="phone", nullable=False)
    community: Mapped[str | None] = mapped_column(String(200), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    immediate_safety_concerns: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    law_enforcement_involved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    law_enforcement_file_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    law_enforcement_officer_info: Mapped[str | None] = mapped_column(String(300), nullable=True)

    assigned_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_worker_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    assigned_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    origin_agency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    people: Mapped[list["ReferralPerson"]] = relationship(
        "ReferralPerson", back_populates="referral", cascade="all, delete-orphan", lazy="selectin"
    )
    reporter: Mapped["ReferralReporter | None"] = relationship(
        "ReferralReporter", back_populates="referral", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    incidents: Mapped[list["ReferralIncident"]] = relationship(
        "ReferralIncident", back_populates="referral", cascade="all, delete-orphan", lazy="selectin"
    )
    concerns: Mapped[list["ReferralConcern"]] = relationship(
        "ReferralConcern", back_populates="referral", cascade="all, delete-orphan", lazy="selectin"
    )
    dispositions: Mapped[list["ChildDisposition"]] = relationship(
        "ChildDisposition", back_populates="referral", cascade="all, delete-orphan", lazy="selectin"
    )
    decision: Mapped["IntakeDecision | None"] = relationship(
        "IntakeDecision", back_populates="referral", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    outgoing_links: Mapped[list["ReferralLink"]] = relationship(
        "ReferralLink", foreign_keys="ReferralLink.source_referral_id", back_populates="source_referral", lazy="selectin"
    )


class ReferralPerson(Base, TimestampMixin):
    """Associates a canonical Person to a Referral with domain role and caregiver context."""
    __tablename__ = "referral_people"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # child, parent, guardian, alleged_concern, relative, other_adult
    relationship_to_child: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_primary_caregiver: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_subject_of_concern: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral: Mapped["Referral"] = relationship("Referral", back_populates="people")
    person: Mapped["Person"] = relationship("Person", lazy="joined")

    __table_args__ = (
        Index("ix_referral_people_referral_person", "referral_id", "person_id"),
        Index("ix_referral_people_role", "role"),
    )


class ReferralReporter(Base, TimestampMixin):
    """Confidential reporter details container. Protected by strict permissions."""
    __tablename__ = "referral_reporters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_mandated_reporter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wants_notification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    reporter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    preferred_contact_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relationship_to_family: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reporter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral: Mapped["Referral"] = relationship("Referral", back_populates="reporter")


class ReferralIncident(Base, TimestampMixin):
    """Specific allegation/incident event captured during intake."""
    __tablename__ = "referral_incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    incident_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    community: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    law_enforcement_involved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    police_file_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    officer_info: Mapped[str | None] = mapped_column(String(300), nullable=True)
    immediate_danger: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    referral: Mapped["Referral"] = relationship("Referral", back_populates="incidents")


class ReferralConcern(Base, TimestampMixin):
    """Categorized screening concerns and harm types."""
    __tablename__ = "referral_concerns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concern_type: Mapped[str] = mapped_column(String(100), nullable=False)  # physical_abuse, neglect, domestic_violence, etc.
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="Moderate", nullable=False)  # Low, Moderate, High, Critical
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral: Mapped["Referral"] = relationship("Referral", back_populates="concerns")

    __table_args__ = (
        Index("ix_referral_concerns_type", "concern_type"),
    )


class ChildDisposition(Base, TimestampMixin):
    """Mandatory per-child screening disposition (Protection, Prevention, Screen Out, External)."""
    __tablename__ = "child_dispositions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # PROTECTION, PREVENTION, SCREEN_OUT, EXTERNAL_REFERRAL, POST_MAJORITY
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    
    destination_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    destination_program: Mapped[str | None] = mapped_column(String(200), nullable=True)
    external_agency_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_referral_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    resulting_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL", use_alter=True), nullable=True, index=True
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_state: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)

    referral: Mapped["Referral"] = relationship("Referral", back_populates="dispositions")
    person: Mapped["Person"] = relationship("Person", lazy="joined")


class IntakeDecision(Base, TimestampMixin):
    """Formal decision recommendation and supervisor submission lifecycle state."""
    __tablename__ = "intake_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    overall_recommendation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
    supervisor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    returned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    referral: Mapped["Referral"] = relationship("Referral", back_populates="decision")


class ReferralLink(Base, TimestampMixin):
    """Relational cross-link between two Referrals (e.g. duplicate reports, related incidents)."""
    __tablename__ = "referral_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    link_type: Mapped[str] = mapped_column(String(50), nullable=False)  # duplicate_report, related_incident, prior_history, split_family
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    source_referral: Mapped["Referral"] = relationship(
        "Referral", foreign_keys=[source_referral_id], back_populates="outgoing_links"
    )
    target_referral: Mapped["Referral"] = relationship("Referral", foreign_keys=[target_referral_id])

    __table_args__ = (
        UniqueConstraint("source_referral_id", "target_referral_id", "link_type", name="uq_referral_links_source_target_type"),
    )
