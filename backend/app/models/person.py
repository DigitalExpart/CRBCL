"""Person canonical human identity and related normalized profile models."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class Person(Base, AuditMixin, SoftDeleteMixin):
    """Canonical human identity across clients, relatives, collaterals, and community members."""

    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(200), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_name: Mapped[str] = mapped_column(String(200), nullable=False)
    preferred_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    aliases: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated or searchable aliases

    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(200), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(100), default="English", nullable=False)
    languages_spoken: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Identifiers
    treaty_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    band_nation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    indigenous_identity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    health_card_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Primary Contact & Emergency Contact
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Economic & Employment
    source_of_income: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employment_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employment_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Social Media / Additional
    social_media_handles: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    addresses: Mapped[list[PersonAddress]] = relationship("PersonAddress", back_populates="person", lazy="selectin")
    contacts: Mapped[list[PersonContact]] = relationship("PersonContact", back_populates="person", lazy="selectin")
    physical_description: Mapped[PersonPhysicalDescription | None] = relationship(
        "PersonPhysicalDescription", back_populates="person", uselist=False, lazy="selectin"
    )
    cultural_profile: Mapped[PersonCulturalProfile | None] = relationship(
        "PersonCulturalProfile", back_populates="person", uselist=False, lazy="selectin"
    )
    strengths: Mapped[list[PersonStrength]] = relationship("PersonStrength", back_populates="person", lazy="selectin")
    challenges: Mapped[list[PersonChallenge]] = relationship(
        "PersonChallenge", back_populates="person", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_persons_name_trgm", "first_name", "last_name"),
        Index("ix_persons_dob", "date_of_birth"),
        Index("ix_persons_treaty", "treaty_number"),
        Index("ix_persons_health_card", "health_card_number"),
    )


class PersonAddress(Base, TimestampMixin):
    """Historical and primary address tracking for a person."""

    __tablename__ = "person_addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(String(50), default="Residential", nullable=False)
    address_line_1: Mapped[str] = mapped_column(String(500), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(200), default="Regina", nullable=False)
    province: Mapped[str] = mapped_column(String(100), default="Saskatchewan", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Canada", nullable=False)
    on_reserve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    person: Mapped[Person] = relationship("Person", back_populates="addresses")


class PersonContact(Base, TimestampMixin):
    """Normalized contact entry (phones, emails, social accounts)."""

    __tablename__ = "person_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Phone, Email, Social, Other
    value: Mapped[str] = mapped_column(String(320), nullable=False)
    label: Mapped[str] = mapped_column(String(100), default="Primary", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_contact_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    person: Mapped[Person] = relationship("Person", back_populates="contacts")


class PersonPhysicalDescription(Base, TimestampMixin):
    """Physical characteristics and distinguishing features."""

    __tablename__ = "person_physical_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    eye_colour: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hair_colour: Mapped[str | None] = mapped_column(String(50), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    tattoos: Mapped[str | None] = mapped_column(Text, nullable=True)
    piercings: Mapped[str | None] = mapped_column(Text, nullable=True)
    birthmarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    scars: Mapped[str | None] = mapped_column(Text, nullable=True)
    distinguishing_marks: Mapped[str | None] = mapped_column(Text, nullable=True)
    glasses: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_lenses: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person: Mapped[Person] = relationship("Person", back_populates="physical_description")


class PersonCulturalProfile(Base, TimestampMixin):
    """Cultural engagement, traditions, ceremonies, and linguistic goals."""

    __tablename__ = "person_cultural_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    cultural_connections: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceremonies: Mapped[str | None] = mapped_column(Text, nullable=True)
    elders_connected: Mapped[str | None] = mapped_column(Text, nullable=True)
    land_based_activities: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    dietary_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracurricular_activities: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person: Mapped[Person] = relationship("Person", back_populates="cultural_profile")


class PersonStrength(Base, TimestampMixin):
    """Relational strengths mapped to configurable lookup categories."""

    __tablename__ = "person_strengths"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lookup_value_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person: Mapped[Person] = relationship("Person", back_populates="strengths")


class PersonChallenge(Base, TimestampMixin):
    """Relational challenges/alerts mapped to configurable lookup categories."""

    __tablename__ = "person_challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lookup_value_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="Moderate", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person: Mapped[Person] = relationship("Person", back_populates="challenges")


class PersonMerge(Base):
    """Immutable audit trail for controlled person duplicate merges."""

    __tablename__ = "person_merges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    target_person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    merged_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    merged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
