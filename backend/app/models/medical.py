"""Client medical profile, allergies, chronic conditions, and medication history."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class ClientMedicalProfile(Base, TimestampMixin):
    """Overview medical profile for a client."""
    __tablename__ = "client_medical_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    dental_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    mental_health_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    chemical_dependency_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_physician_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_physician_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primary_physician_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class ClientAllergy(Base, TimestampMixin):
    """Allergies and adverse reactions."""
    __tablename__ = "client_allergies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    reaction: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="Moderate", nullable=False)  # Mild, Moderate, Severe, Life-Threatening
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ClientMedicalCondition(Base, TimestampMixin):
    """Diagnosed chronic and acute medical conditions."""
    __tablename__ = "client_medical_conditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_name: Mapped[str] = mapped_column(String(300), nullable=False)
    diagnosed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_chronic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ClientMedication(Base, TimestampMixin):
    """Historical and active prescription medications."""
    __tablename__ = "client_medications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_name: Mapped[str] = mapped_column(String(300), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str] = mapped_column(String(100), default="Oral", nullable=False)
    prescriber_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    prescriber_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False)  # Active, Discontinued, Completed, Paused
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
