"""Sprint B — Clinical Notes, Programs, Grants, Incidents & Appointments SQLAlchemy Models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

# ==========================================
# 1. CLINICAL / LPN NOTES
# ==========================================


class ClinicalNote(Base, AuditMixin, SoftDeleteMixin):
    """Dedicated Clinical / LPN note record with immutability lifecycle."""

    __tablename__ = "clinical_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    note_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="LPN_OBSERVATION", index=True
    )  # LPN_OBSERVATION, MEDICATION_LOG, VITAL_SIGNS, CLINICAL_ASSESSMENT
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    confidentiality: Mapped[str] = mapped_column(
        String(50), nullable=False, default="CONFIDENTIAL"
    )  # STANDARD, CONFIDENTIAL, RESTRICTED
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFT", index=True
    )  # DRAFT, COMPLETE, LOCKED
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    client = relationship("Client", foreign_keys=[client_id], lazy="joined")
    case = relationship("Case", foreign_keys=[case_id], lazy="joined")
    author = relationship("User", foreign_keys=[author_id], lazy="joined")
    addenda = relationship("ClinicalNoteAddendum", back_populates="clinical_note", cascade="all, delete-orphan")


class ClinicalNoteAddendum(Base, AuditMixin):
    """Addendum attached to a locked Clinical Note."""

    __tablename__ = "clinical_note_addenda"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinical_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinical_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    narrative: Mapped[str] = mapped_column(Text, nullable=False)

    clinical_note = relationship("ClinicalNote", back_populates="addenda")
    author = relationship("User", foreign_keys=[author_id], lazy="joined")


# ==========================================
# 2. PROGRAMS (COMMUNITY & CULTURAL)
# ==========================================


class Program(Base, AuditMixin, SoftDeleteMixin):
    """Community, youth, or cultural program entity."""

    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Cultural Programs", index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, PLANNING, COMPLETED, SUSPENDED
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    capacity: Mapped[int] = mapped_column(nullable=False, default=20)
    enrolled_count: Mapped[int] = mapped_column(nullable=False, default=0)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    coordinator_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)


# ==========================================
# 3. FUNDING GRANTS
# ==========================================


class FundingGrant(Base, AuditMixin, SoftDeleteMixin):
    """Funding grant record."""

    __tablename__ = "funding_grants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grant_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    funder_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # PENDING, ACTIVE, EXPIRED, CLOSED
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ==========================================
# 4. GENERAL INCIDENTS
# ==========================================


class Incident(Base, AuditMixin, SoftDeleteMixin):
    """General organizational or critical incident report (distinct from Fleet vehicle incidents)."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Critical Incident", index=True)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MEDIUM", index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OPEN", index=True
    )  # OPEN, UNDER_REVIEW, RESOLVED, CLOSED
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actions_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by_name: Mapped[str] = mapped_column(String(150), nullable=False)
    witnesses: Mapped[str | None] = mapped_column(Text, nullable=True)

    client = relationship("Client", foreign_keys=[client_id], lazy="joined")
    case = relationship("Case", foreign_keys=[case_id], lazy="joined")


# ==========================================
# 5. APPOINTMENTS
# ==========================================


class Appointment(Base, AuditMixin, SoftDeleteMixin):
    """Client/Family operational appointment."""

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    appointment_type: Mapped[str] = mapped_column(String(100), nullable=False, default="General", index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, default=60)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SCHEDULED", index=True
    )  # SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    client = relationship("Client", foreign_keys=[client_id], lazy="joined")
    case = relationship("Case", foreign_keys=[case_id], lazy="joined")
