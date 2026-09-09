"""Caregiver training domain model (caregivers are Persons, not Employees)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.person import Person
    from app.models.placement_home import PlacementHome
    from app.models.user import User


class CaregiverTraining(Base, AuditMixin, SoftDeleteMixin):
    """Caregiver pre-service, CPR, cultural safety, and specialized training records.

    Note: Caregivers are Person records, NOT Employee records.
    """

    __tablename__ = "caregiver_trainings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    placement_home_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    training_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # PRE_SERVICE_PRIDE, CPR_FIRST_AID, TRAUMA_INFORMED_CARE, CULTURAL_SAFETY, SUICIDE_PREVENTION, MEDICATION_ADMINISTRATION, OTHER
    course_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completion_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="COMPLETED", index=True
    )  # COMPLETED, IN_PROGRESS, EXPIRED, WAIVED
    renewal_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    person: Mapped[Person] = relationship("Person", foreign_keys=[person_id], lazy="joined")
    placement_home: Mapped[PlacementHome | None] = relationship(
        "PlacementHome", back_populates="trainings", foreign_keys=[placement_home_id], lazy="joined"
    )
    document: Mapped[Document | None] = relationship("Document", foreign_keys=[document_id], lazy="joined")
    verifier: Mapped[User | None] = relationship("User", foreign_keys=[verified_by], lazy="joined")
