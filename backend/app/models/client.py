"""Client model — individuals receiving services linked to canonical Person."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class Client(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(200), nullable=False)
    last_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Pending Intake", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="Low", nullable=False)

    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(200), nullable=True)
    province: Mapped[str] = mapped_column(String(100), default="Saskatchewan", nullable=False)

    indigenous_identity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    band_nation: Mapped[str | None] = mapped_column(String(200), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Team assignment for scoped access
    assigned_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Relationships
    person: Mapped["Person | None"] = relationship("Person", lazy="selectin")  # noqa: F821
    medical_profile: Mapped["ClientMedicalProfile | None"] = relationship(  # noqa: F821
        "ClientMedicalProfile", back_populates=None, uselist=False, lazy="selectin"
    )
    allergies: Mapped[list["ClientAllergy"]] = relationship("ClientAllergy", lazy="selectin")  # noqa: F821
    conditions: Mapped[list["ClientMedicalCondition"]] = relationship("ClientMedicalCondition", lazy="selectin")  # noqa: F821
    medications: Mapped[list["ClientMedication"]] = relationship("ClientMedication", lazy="selectin")  # noqa: F821
    providers: Mapped[list["ClientProvider"]] = relationship("ClientProvider", lazy="selectin")  # noqa: F821
    school_enrolments: Mapped[list["ClientSchoolEnrolment"]] = relationship("ClientSchoolEnrolment", lazy="selectin")  # noqa: F821

    __table_args__ = (
        Index("ix_clients_name_trgm", "first_name", "last_name"),
        Index("ix_clients_status", "status"),
        Index("ix_clients_risk_level", "risk_level"),
    )
