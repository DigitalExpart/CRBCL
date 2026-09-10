"""Resource Home Complaints and Investigations model (Sprint 3).

Tracks complaints, allegations, investigation activities, finalized findings,
and dispositions with role-based privacy and immutability controls.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.placement_home import PlacementHome
    from app.models.sprint_b_models import Incident
    from app.models.user import User


class ResourceComplaint(Base, AuditMixin, SoftDeleteMixin):
    """Authoritative complaint and investigation record against a Resource Home."""

    __tablename__ = "resource_complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    complainant_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ANONYMOUS", index=True
    )  # COMMUNITY_MEMBER, FOSTER_CHILD, BIRTH_PARENT, CAREGIVER, COLLATERAL, AGENCY_STAFF, ANONYMOUS
    complainant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Sensitive
    complainant_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Sensitive
    received_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    complaint_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="CARE_STANDARDS", index=True
    )  # CARE_STANDARDS, PHYSICAL_ENVIRONMENT, SAFETY_CONCERN, BEHAVIOUR_MANAGEMENT, COMMUNICATION, POLICY_VIOLATION, OTHER
    allegation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MEDIUM", index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL
    assigned_investigator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="RECEIVED", index=True
    )  # RECEIVED, ASSIGNED, UNDER_INVESTIGATION, FINDINGS_PENDING, DISPOSITION_REVIEW, RESOLVED, CLOSED
    investigation_activities: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    findings_finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    findings_finalized_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposition: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )  # SUBSTANTIATED, UNSUBSTANTIATED, INCONCLUSIVE, RESOLVED_INFORMALLY, POLICY_ACTION_REQUIRED
    disposition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposition_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    disposition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    placement_home: Mapped[PlacementHome] = relationship("PlacementHome", back_populates="complaints")
    investigator: Mapped[User | None] = relationship("User", foreign_keys=[assigned_investigator_id], lazy="joined")
    finalizer: Mapped[User | None] = relationship("User", foreign_keys=[findings_finalized_by], lazy="joined")
    dispositioner: Mapped[User | None] = relationship("User", foreign_keys=[disposition_by_id], lazy="joined")
    incident: Mapped[Incident | None] = relationship("Incident", foreign_keys=[incident_id], lazy="joined")
    document: Mapped[Document | None] = relationship("Document", foreign_keys=[document_id], lazy="joined")
