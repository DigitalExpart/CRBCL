"""Placement Home and Facility domain models: homes, members, licensing, inspections/visits, and contact logs."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.person import Person
    from app.models.placement import PlacementEpisode
    from app.models.provider import Provider
    from app.models.user import User


class PlacementHome(Base, AuditMixin, SoftDeleteMixin):
    """Authorized placement home, foster home, kinship home, or care facility."""

    __tablename__ = "placement_homes"
    __table_args__ = (CheckConstraint("total_capacity >= 0", name="ck_placement_homes_capacity_positive"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    home_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="LICENSED_FOSTER", index=True
    )  # LICENSED_FOSTER, THERAPEUTIC, KINSHIP, RELATIVE, FACILITY
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, INACTIVE, ON_HOLD, CLOSED
    licensing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UNLICENSED", index=True
    )  # UNLICENSED, APPLICATION, PENDING, ACTIVE, SUSPENDED, EXPIRED, REVOKED, CLOSED
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Regina")
    province: Mapped[str] = mapped_column(String(100), nullable=False, default="Saskatchewan")
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    community: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    primary_caregiver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    intake_criteria_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata_", JSONB, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    provider: Mapped[Provider | None] = relationship("Provider", foreign_keys=[provider_id], lazy="joined")
    archiver: Mapped[User | None] = relationship("User", foreign_keys=[archived_by], lazy="noload")
    members: Mapped[list[PlacementHomeMember]] = relationship(
        "PlacementHomeMember", back_populates="placement_home", cascade="all, delete-orphan", lazy="selectin"
    )
    licenses: Mapped[list[PlacementHomeLicense]] = relationship(
        "PlacementHomeLicense",
        back_populates="placement_home",
        cascade="all, delete-orphan",
        order_by="desc(PlacementHomeLicense.effective_date)",
        lazy="selectin",
    )
    visits: Mapped[list[PlacementHomeVisit]] = relationship(
        "PlacementHomeVisit",
        back_populates="placement_home",
        cascade="all, delete-orphan",
        order_by="desc(PlacementHomeVisit.visit_date)",
        lazy="selectin",
    )
    contact_logs: Mapped[list[PlacementHomeContactLog]] = relationship(
        "PlacementHomeContactLog",
        back_populates="placement_home",
        cascade="all, delete-orphan",
        order_by="desc(PlacementHomeContactLog.contact_date)",
        lazy="selectin",
    )
    placements: Mapped[list[PlacementEpisode]] = relationship(
        "PlacementEpisode", back_populates="placement_home", lazy="selectin"
    )
    assessments: Mapped[list[Assessment]] = relationship("Assessment", back_populates="placement_home", lazy="selectin")


class PlacementHomeMember(Base, AuditMixin, SoftDeleteMixin):
    """Caregiver or resident household member attached to a placement home."""

    __tablename__ = "placement_home_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PRIMARY_CAREGIVER"
    )  # PRIMARY_CAREGIVER, SECONDARY_CAREGIVER, ADULT_HOUSEHOLD_MEMBER, YOUTH_HOUSEHOLD_MEMBER, OTHER
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="members")
    person: Mapped[Person] = relationship("Person", foreign_keys=[person_id], lazy="joined")


class PlacementHomeLicense(Base, AuditMixin, SoftDeleteMixin):
    """Historical and active licensing terms for a placement home."""

    __tablename__ = "placement_home_licenses"
    __table_args__ = (CheckConstraint("expiry_date >= effective_date", name="ck_placement_home_licenses_dates_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    license_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    license_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="STANDARD_FOSTER"
    )  # PROVISIONAL, STANDARD_FOSTER, SPECIALIZED_THERAPEUTIC, KINSHIP_APPROVED, CUSTOMARY_CARE
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # APPLICATION, PENDING, ACTIVE, SUSPENDED, EXPIRED, REVOKED, CLOSED
    application_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issuing_authority: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Ministry of Social Services / First Nation Authority"
    )
    max_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="licenses")


class PlacementHomeVisit(Base, AuditMixin, SoftDeleteMixin):
    """Routine, unannounced, or annual inspection and support visit to a placement home."""

    __tablename__ = "placement_home_visits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    visit_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ROUTINE_INSPECTION"
    )  # ROUTINE_INSPECTION, ANNUAL_REVIEW, UNANNOUNCED_CHECK, INCIDENT_FOLLOWUP, SUPPORT_VISIT
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="COMPLETED"
    )  # SCHEDULED, COMPLETED, CANCELLED

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="visits")
    worker: Mapped[User] = relationship("User", foreign_keys=[worker_id], lazy="joined")


class PlacementHomeContactLog(Base, AuditMixin, SoftDeleteMixin):
    """Direct contact log with placement home caregivers and household members."""

    __tablename__ = "placement_home_contact_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    contact_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PHONE"
    )  # PHONE, EMAIL, IN_PERSON, VIDEO, WRITTEN
    contact_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="contact_logs")
    person: Mapped[Person | None] = relationship("Person", foreign_keys=[person_id], lazy="joined")
    worker: Mapped[User] = relationship("User", foreign_keys=[worker_id], lazy="joined")
