"""Family membership, directional relationships, and residential households."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class FamilyMember(Base, TimestampMixin):
    """Membership of a person in a family entity."""

    __tablename__ = "family_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(100), default="Member", nullable=False
    )  # Parent, Child, Guardian, Kinship Caregiver, Elder
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person: Mapped[Person] = relationship("Person", lazy="selectin")  # noqa: F821

    __table_args__ = (Index("ix_family_members_family_person", "family_id", "person_id"),)


class FamilyRelationship(Base, TimestampMixin):
    """
    Directional interpersonal relationship between two persons.
    Example: person_a_id is [relationship_type] of person_b_id (e.g. mother_of, guardian_of, sibling_of).
    """

    __tablename__ = "family_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="CASCADE"), nullable=True, index=True
    )
    person_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # mother_of, father_of, sibling_of, grandparent_of, aunt_of, uncle_of, guardian_of, spouse_of, cousin_of, other
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    person_a: Mapped[Person] = relationship("Person", foreign_keys=[person_a_id], lazy="selectin")  # noqa: F821
    person_b: Mapped[Person] = relationship("Person", foreign_keys=[person_b_id], lazy="selectin")  # noqa: F821

    __table_args__ = (Index("ix_family_relationships_pair", "person_a_id", "person_b_id"),)


class Household(Base, TimestampMixin):
    """A physical residential living arrangement distinct from biological family."""

    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    address_line_1: Mapped[str] = mapped_column(String(500), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(200), default="Regina", nullable=False)
    province: Mapped[str] = mapped_column(String(100), default="Saskatchewan", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_reserve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    memberships: Mapped[list[HouseholdMembership]] = relationship(
        "HouseholdMembership", back_populates="household", lazy="selectin"
    )


class HouseholdMembership(Base, TimestampMixin):
    """Links a person to a residential household during a period."""

    __tablename__ = "household_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(100), default="Resident", nullable=False
    )  # Head of Household, Resident, Temporary, Dependent
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    household: Mapped[Household] = relationship("Household", back_populates="memberships")
    person: Mapped[Person] = relationship("Person", lazy="selectin")  # noqa: F821

    __table_args__ = (Index("ix_household_memberships_h_p", "household_id", "person_id"),)
