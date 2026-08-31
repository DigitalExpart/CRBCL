"""Placement, Active Efforts, Removals, Episodes, Respite, Discharge, Permanency, Visitation, Court & Background Checks Models."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class ActiveEffort(Base, AuditMixin, SoftDeleteMixin):
    """Active Efforts provided to preserve the Indigenous family under customary care standards."""

    __tablename__ = "active_efforts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    effort_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    service_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, default="ONGOING")
    barriers_encountered: Mapped[str | None] = mapped_column(Text, nullable=True)
    remedial_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    case = relationship("Case", backref="active_efforts")
    worker = relationship("User", foreign_keys=[worker_id])


class BackgroundCheck(Base, AuditMixin, SoftDeleteMixin):
    """Polymorphic background check screening records for clients, family members, providers, and volunteers."""

    __tablename__ = "background_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CLIENT, PERSON, PLACEMENT_PROVIDER, VOLUNTEER, STAFF, OTHER
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CRIMINAL_RECORD, CHILD_ABUSE_REGISTRY, VULNERABLE_SECTOR, REFERENCE_CHECK
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, PASSED, FAILED, CONDITIONAL, EXPIRED
    request_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    conducted_by_agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clearance_reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_assessment_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_eligible_for_placement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    adjudicated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    adjudicated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    adjudicator = relationship("User", foreign_keys=[adjudicated_by])


class InHomePlacement(Base, AuditMixin, SoftDeleteMixin):
    """In-home family preservation placement under departmental supervision."""

    __tablename__ = "in_home_placements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    primary_caregiver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    caregiver_relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)  # ACTIVE, ENDED, ESCALATED_TO_REMOVAL
    supervision_level: Mapped[str] = mapped_column(String(50), nullable=False, default="STANDARD")  # MINIMAL, STANDARD, INTENSIVE
    safety_monitoring_frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="WEEKLY")  # DAILY, WEEKLY, BIWEEKLY, MONTHLY
    support_services_provided: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("Case", backref="in_home_placements")
    child = relationship("Person", foreign_keys=[child_id])
    caregiver = relationship("Person", foreign_keys=[primary_caregiver_id])


class RemovalEpisode(Base, AuditMixin, SoftDeleteMixin):
    """Legal and physical removal event taking a child into protective care."""

    __tablename__ = "removal_episodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    removal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    removal_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    removal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # VOLUNTARY, EMERGENCY_ORDER, COURT_APPREHENSION, TEMPORARY_CUSTODY
    authority_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CHILD_WELFARE_WARRANT, CONSENT_AGREEMENT, POLICE_ASSISTANCE, COURT_ORDER
    legal_authority_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason_for_removal: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_safety_threat: Mapped[str | None] = mapped_column(Text, nullable=True)
    removal_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accompanying_officers: Mapped[str | None] = mapped_column(String(255), nullable=True)
    child_condition_at_removal: Mapped[str | None] = mapped_column(Text, nullable=True)
    belongings_inventoried: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLETED")  # ACTIVE, COMPLETED, CANCELLED

    case = relationship("Case", backref="removal_episodes")
    child = relationship("Person", foreign_keys=[child_id])
    placements = relationship("PlacementEpisode", back_populates="removal_episode")


class PlacementEpisode(Base, AuditMixin, SoftDeleteMixin):
    """Primary out-of-home placement episode for a child."""

    __tablename__ = "placement_episodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    removal_episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("removal_episodes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    placement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # KINSHIP, CUSTOMARY_CARE, FOSTER_HOME, GROUP_HOME, INDEPENDENT_LIVING, OTHER
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)  # ACTIVE, DISRUPTED, PLANNED_DISCHARGE, TRANSFERRED, COMPLETED
    primary_caregiver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    per_diem_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cultural_plan_in_place: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    placement_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("Case", backref="placement_episodes")
    child = relationship("Person", foreign_keys=[child_id])
    removal_episode = relationship("RemovalEpisode", back_populates="placements")
    respite_episodes = relationship("RespiteEpisode", back_populates="placement_episode", cascade="all, delete-orphan")
    discharge_episode = relationship("DischargeEpisode", back_populates="placement_episode", uselist=False, cascade="all, delete-orphan")


class RespiteEpisode(Base, AuditMixin, SoftDeleteMixin):
    """Temporary respite stay subordinate to an active primary placement."""

    __tablename__ = "respite_episodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_episodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    respite_provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    respite_type: Mapped[str] = mapped_column(String(50), nullable=False, default="PLANNED")  # PLANNED, EMERGENCY
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHEDULED")  # SCHEDULED, ACTIVE, COMPLETED, CANCELLED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    placement_episode = relationship("PlacementEpisode", back_populates="respite_episodes")


class DischargeEpisode(Base, AuditMixin, SoftDeleteMixin):
    """Formal discharge and conclusion of a placement episode."""

    __tablename__ = "discharge_episodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_episodes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    discharge_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    discharge_type: Mapped[str] = mapped_column(String(50), nullable=False)  # REUNIFICATION, CUSTOMARY_ADOPTION, PERMANENT_KINSHIP, AGING_OUT, TRANSFER, OTHER
    destination_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination_relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    post_discharge_supervision_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    discharge_readiness_assessed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    placement_episode = relationship("PlacementEpisode", back_populates="discharge_episode")
    approver = relationship("User", foreign_keys=[approved_by])


class PermanencyPlan(Base, AuditMixin, SoftDeleteMixin):
    """Long-term permanency and cultural connection planning for a child."""

    __tablename__ = "permanency_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    primary_goal: Mapped[str] = mapped_column(String(50), nullable=False)  # REUNIFICATION, CUSTOMARY_CARE, KINSHIP_LEGAL_CUSTODY, ADOPTION, INDEPENDENT_LIVING, OTHER
    concurrent_goal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT", index=True)  # DRAFT, ACTIVE, ACHIEVED, MODIFIED, CLOSED
    cultural_heritage_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    sibling_co_placement_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_frequency_months: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    established_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("Case", backref="permanency_plans")
    child = relationship("Person", foreign_keys=[child_id])
    creator = relationship("User", foreign_keys=[established_by])
    approver = relationship("User", foreign_keys=[approved_by])


class VisitationPlan(Base, AuditMixin, SoftDeleteMixin):
    """Family contact and visitation schedule for a child in out-of-home care."""

    __tablename__ = "visitation_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_names: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="WEEKLY")  # DAILY, WEEKLY, BIWEEKLY, MONTHLY, SPECIAL_OCCASIONS
    duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    supervision_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supervisor_type: Mapped[str] = mapped_column(String(50), nullable=False, default="CASE_WORKER")  # CASE_WORKER, FAMILY_SUPPORT_WORKER, UNMONITORED, THIRD_PARTY
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)  # ACTIVE, SUSPENDED, MODIFIED, TERMINATED
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("Case", backref="visitation_plans")
    child = relationship("Person", foreign_keys=[child_id])


class CourtEvent(Base, AuditMixin, SoftDeleteMixin):
    """Child protection court hearing, legal proceeding, or band representation event."""

    __tablename__ = "court_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hearing_type: Mapped[str] = mapped_column(String(50), nullable=False)  # INITIAL_APPEARANCE, PROTECTION_HEARING, TEMPORARY_CUSTODY_REVIEW, PERMANENCY_HEARING, STATUS_REVIEW, BAND_REPRESENTATION_HEARING, OTHER
    court_docket_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    court_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    judge_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hearing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hearing_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    outcome_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    orders_issued: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_counsel_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    band_representative_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_court_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHEDULED", index=True)  # SCHEDULED, COMPLETED, ADJOURNED, CANCELLED

    case = relationship("Case", backref="court_events")
    child = relationship("Person", foreign_keys=[child_id])
