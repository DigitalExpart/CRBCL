"""Case note model with Phase 4 extensions: People, Attachments, Addenda, and Immutability Locking."""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class CaseNote(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "case_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), default="Progress Note", nullable=False)
    
    # Phase 4 Metadata
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_well_child_checkup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    appointment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    next_appointment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    notify_team: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Immutability & Status
    status: Mapped[str] = mapped_column(
        String(50), default="COMPLETED", nullable=False
    )  # DRAFT, COMPLETED, LOCKED
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Relationships
    case = relationship("Case", back_populates="case_notes")
    people = relationship("CaseNotePerson", back_populates="case_note", cascade="all, delete-orphan")
    attachments = relationship("CaseNoteAttachment", back_populates="case_note", cascade="all, delete-orphan")
    addenda = relationship("CaseNoteAddendum", back_populates="case_note", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_case_notes_status", "status"),
        Index("ix_case_notes_contact_type", "contact_type"),
    )


class CaseNotePerson(Base):
    """People present or involved during the recorded contact."""
    __tablename__ = "case_note_people"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case_note = relationship("CaseNote", back_populates="people")
    person = relationship("Person", lazy="joined")


class CaseNoteAttachment(Base):
    """Uploaded attachments specifically linked to the case note."""
    __tablename__ = "case_note_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case_note = relationship("CaseNote", back_populates="attachments")


class CaseNoteAddendum(Base):
    """Immutable addenda appended to locked case notes for corrections or clarifications."""
    __tablename__ = "case_note_addenda"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case_note = relationship("CaseNote", back_populates="addenda")
    author = relationship("User", foreign_keys=[created_by], lazy="joined")
