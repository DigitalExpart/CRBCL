"""Provider pool models for physicians, counsellors, specialists, and cultural helpers."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Provider(Base, TimestampMixin):
    """Reusable provider pool entity."""
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Physician, Therapist, Counsellor, Dentist, Cultural Service, etc.
    organization_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    locations: Mapped[list[ProviderLocation]] = relationship("ProviderLocation", back_populates="provider", lazy="selectin")
    specialties: Mapped[list[ProviderSpecialty]] = relationship("ProviderSpecialty", back_populates="provider", lazy="selectin")


class ProviderLocation(Base, TimestampMixin):
    """Locations / clinics associated with a provider."""
    __tablename__ = "provider_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_line_1: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(200), default="Regina", nullable=False)
    province: Mapped[str] = mapped_column(String(100), default="Saskatchewan", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    provider: Mapped[Provider] = relationship("Provider", back_populates="locations")


class ProviderSpecialty(Base, TimestampMixin):
    """Specialty areas for a provider."""
    __tablename__ = "provider_specialties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    specialty: Mapped[str] = mapped_column(String(200), nullable=False)

    provider: Mapped[Provider] = relationship("Provider", back_populates="specialties")


class ClientProvider(Base, TimestampMixin):
    """Linkage connecting a client to their assigned healthcare or cultural provider."""
    __tablename__ = "client_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(100), default="Primary Care", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    provider: Mapped[Provider] = relationship("Provider", lazy="selectin")
