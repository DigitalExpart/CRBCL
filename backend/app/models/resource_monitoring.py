"""Resource Home Monitoring model (Sprint 3).

Tracks periodic/monthly ongoing monitoring contact separate from annual licensing inspections.
Preserves historical audit trail without overwriting past visits.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.placement_home import PlacementHome, PlacementHomeVisit
    from app.models.user import User


class ResourceHomeMonitoring(Base, AuditMixin, SoftDeleteMixin):
    """Periodic or ongoing monitoring contact record with a Resource Home."""

    __tablename__ = "resource_home_monitorings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    contact_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    contact_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="IN_PERSON"
    )  # IN_PERSON, HOME_VISIT, PHONE, VIDEO, COLLATERAL
    child_interview_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    caregiver_interview_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_review_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    corrective_action_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corrective_action_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_home_visits.id", ondelete="SET NULL"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="COMPLETED", index=True
    )  # SCHEDULED, COMPLETED, CANCELLED
    cadence_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="monitorings")
    worker: Mapped[User] = relationship("User", foreign_keys=[worker_id], lazy="joined")
    visit: Mapped[PlacementHomeVisit | None] = relationship("PlacementHomeVisit", foreign_keys=[visit_id], lazy="joined")
    document: Mapped[Document | None] = relationship("Document", foreign_keys=[document_id], lazy="joined")
