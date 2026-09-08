"""Resource Recruitment domain models.

This module defines the core tables for the Resource Unit Sprint 1:

* **ResourceRecruitment** - Authoritative application record for a caregiver household.
* **ResourceRecruitmentApplicant** - Links recruitment application to canonical `Person` records.
* **ResourceRecruitmentHistory** - Append-only audit of state transitions.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.placement_home import PlacementHome
    from app.models.user import User


class RecruitmentState(str, enum.Enum):
    """Authoritative recruitment pipeline stages."""

    INQUIRY = "INQUIRY"
    ORIENTATION = "ORIENTATION"
    APPLICATION = "APPLICATION"
    ASSESSMENT = "ASSESSMENT"
    APPROVAL_REVIEW = "APPROVAL_REVIEW"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
    ON_HOLD = "ON_HOLD"


class ApplicantRole(str, enum.Enum):
    """Applicant relationship role within a recruitment application."""

    PRIMARY_APPLICANT = "PRIMARY_APPLICANT"
    SECONDARY_APPLICANT = "SECONDARY_APPLICANT"


class ResourceRecruitment(Base, AuditMixin, SoftDeleteMixin):
    """Authoritative caregiver recruitment application."""

    __tablename__ = "resource_recruitments"
    __table_args__ = (
        Index("ix_resource_recruitments_current_state", "current_state"),
        Index("ix_resource_recruitments_resource_home_id", "resource_home_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_home_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="SET NULL"), nullable=True
    )
    current_state: Mapped[RecruitmentState] = mapped_column(
        Enum(RecruitmentState, name="recruitmentstate"), nullable=False, default=RecruitmentState.INQUIRY
    )
    previous_state: Mapped[RecruitmentState | None] = mapped_column(
        Enum(RecruitmentState, name="recruitmentstate"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata_", JSONB, nullable=True)

    # Relationships
    resource_home: Mapped[PlacementHome | None] = relationship(
        "PlacementHome", back_populates="recruitments", lazy="joined"
    )
    applicants: Mapped[list[ResourceRecruitmentApplicant]] = relationship(
        "ResourceRecruitmentApplicant",
        back_populates="recruitment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    history: Mapped[list[ResourceRecruitmentHistory]] = relationship(
        "ResourceRecruitmentHistory",
        back_populates="recruitment",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ResourceRecruitmentHistory.changed_at",
    )


class ResourceRecruitmentApplicant(Base, AuditMixin, SoftDeleteMixin):
    """Association linking a recruitment application to a canonical Person record."""

    __tablename__ = "resource_recruitment_applicants"
    __table_args__ = (
        Index("ix_resource_recruitment_applicants_recruitment_id", "recruitment_id"),
        Index("ix_resource_recruitment_applicants_person_id", "person_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruitment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resource_recruitments.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[ApplicantRole] = mapped_column(
        Enum(ApplicantRole, name="applicantrole"), nullable=False, default=ApplicantRole.PRIMARY_APPLICANT
    )
    snapshot: Mapped[dict[str, Any] | None] = mapped_column("snapshot", JSONB, nullable=True)

    # Relationships
    recruitment: Mapped[ResourceRecruitment] = relationship("ResourceRecruitment", back_populates="applicants")
    person: Mapped[Person] = relationship("Person", lazy="joined")


class ResourceRecruitmentHistory(Base, AuditMixin, SoftDeleteMixin):
    """Append-only audit record of a recruitment state transition."""

    __tablename__ = "resource_recruitment_history"
    __table_args__ = (
        Index("ix_resource_recruitment_history_recruitment_id", "recruitment_id"),
        Index("ix_resource_recruitment_history_changed_at", "changed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruitment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resource_recruitments.id", ondelete="CASCADE"), nullable=False
    )
    from_state: Mapped[RecruitmentState] = mapped_column(
        Enum(RecruitmentState, name="recruitmentstate"), nullable=False
    )
    to_state: Mapped[RecruitmentState] = mapped_column(
        Enum(RecruitmentState, name="recruitmentstate"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    recruitment: Mapped[ResourceRecruitment] = relationship("ResourceRecruitment", back_populates="history")
    changed_by: Mapped[User | None] = relationship("User", lazy="joined")
