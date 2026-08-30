"""School directory and client school enrollment history."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class School(Base, TimestampMixin):
    """School and daycare directory entity."""
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    school_type: Mapped[str] = mapped_column(String(100), default="Elementary", nullable=False)  # Daycare, Elementary, Middle, High, Alternative
    district: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(200), default="Regina", nullable=False)
    province: Mapped[str] = mapped_column(String(100), default="Saskatchewan", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    principal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ClientSchoolEnrolment(Base, TimestampMixin):
    """Client school enrollment records with IEP and attendance tracking."""
    __tablename__ = "client_school_enrolments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grade_level: Mapped[str] = mapped_column(String(50), default="Grade 1", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_iep: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    iep_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    school_contact_person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attendance_concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    school: Mapped["School"] = relationship("School", lazy="selectin")
