"""Caregiver and Resource Home Supports model (Sprint 3).

Tracks supports provided to foster/kinship caregivers (financial, respite, clinical,
counselling, cultural, transportation) while linking financial transactions to existing
ServiceRequests without creating duplicate general ledgers.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.finance import ServiceRequest
    from app.models.person import Person
    from app.models.placement_home import PlacementHome
    from app.models.user import User


class CaregiverSupport(Base, AuditMixin, SoftDeleteMixin):
    """Resource Home and caregiver support services and assistance records."""

    __tablename__ = "caregiver_supports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    support_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    caregiver_person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    support_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="RESPITE", index=True
    )  # FINANCIAL_SUPPORT, RESPITE, CLINICAL_SUPPORT, COUNSELLING, CULTURAL_SUPPORT, TRAINING_SUPPORT, TRANSPORTATION, OTHER
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    provided_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="REQUESTED", index=True
    )  # REQUESTED, APPROVED, IN_PROGRESS, PROVIDED, COMPLETED, DENIED, CANCELLED
    provider_program_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    frequency_duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="supports")
    caregiver: Mapped[Person | None] = relationship("Person", foreign_keys=[caregiver_person_id], lazy="joined")
    worker: Mapped[User] = relationship("User", foreign_keys=[worker_id], lazy="joined")
    service_request: Mapped[ServiceRequest | None] = relationship("ServiceRequest", foreign_keys=[service_request_id], lazy="joined")
    document: Mapped[Document | None] = relationship("Document", foreign_keys=[document_id], lazy="joined")
