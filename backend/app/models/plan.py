from __future__ import annotations

"""Family Wellness Case & Safety Plan domain models (Phase 6)."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.case import Case
    from app.models.family import Family
    from app.models.person import Person
    from app.models.provider import Provider
    from app.models.user import User


class PlanSequence(Base):
    """Atomic monthly sequential counter for plan numbering (PLN-YYYYMM-NNNN)."""

    __tablename__ = "plan_sequences"

    period: Mapped[str] = mapped_column(sa.String(6), primary_key=True)  # '202608'
    last_value: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)


class Plan(Base, TimestampMixin):
    """Master family plan file entity (Safety Plan or Case Plan)."""

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    primary_person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("families.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plan_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, index=True)  # SAFETY_PLAN, CASE_PLAN
    plan_number: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), default="DRAFT", nullable=False, index=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    case: Mapped["Case"] = sa_relationship("Case", foreign_keys=[case_id], lazy="selectin")
    primary_person: Mapped["Person | None"] = sa_relationship("Person", foreign_keys=[primary_person_id], lazy="selectin")
    family: Mapped["Family | None"] = sa_relationship("Family", foreign_keys=[family_id], lazy="selectin")
    creator: Mapped["User"] = sa_relationship("User", foreign_keys=[created_by], lazy="selectin")
    updater: Mapped["User | None"] = sa_relationship("User", foreign_keys=[updated_by], lazy="selectin")

    versions: Mapped[list["PlanVersion"]] = sa_relationship(
        "PlanVersion",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanVersion.version_number.desc()",
        lazy="selectin",
    )
    assessments: Mapped[list["PlanAssessment"]] = sa_relationship(
        "PlanAssessment",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def current_version(self) -> PlanVersion | None:
        if self.versions:
            if self.current_version_id:
                for v in self.versions:
                    if v.id == self.current_version_id:
                        return v
            return self.versions[0]
        return None


class PlanVersion(Base, TimestampMixin):
    """Immutable version snapshot for a Plan."""

    __tablename__ = "plan_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), default="DRAFT", nullable=False, index=True)
    meeting_date: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    meeting_location: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    narrative: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_versions.id", ondelete="SET NULL"), nullable=True
    )
    document_hash: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)  # SHA-256

    finalized_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    locked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    __table_args__ = (sa.UniqueConstraint("plan_id", "version_number", name="uq_plan_version_number"),)

    # Relationships
    plan: Mapped["Plan"] = sa_relationship("Plan", back_populates="versions")
    creator: Mapped["User | None"] = sa_relationship("User", foreign_keys=[created_by], lazy="selectin")
    finalizer: Mapped["User | None"] = sa_relationship("User", foreign_keys=[finalized_by], lazy="selectin")
    locker: Mapped["User | None"] = sa_relationship("User", foreign_keys=[locked_by], lazy="selectin")

    participants: Mapped[list["PlanParticipant"]] = sa_relationship(
        "PlanParticipant",
        back_populates="plan_version",
        cascade="all, delete-orphan",
        order_by="PlanParticipant.name",
        lazy="selectin",
    )
    concerns: Mapped[list["PlanConcern"]] = sa_relationship(
        "PlanConcern",
        back_populates="plan_version",
        cascade="all, delete-orphan",
        order_by="PlanConcern.sort_order",
        lazy="selectin",
    )
    strengths: Mapped[list["PlanStrength"]] = sa_relationship(
        "PlanStrength",
        back_populates="plan_version",
        cascade="all, delete-orphan",
        order_by="PlanStrength.sort_order",
        lazy="selectin",
    )
    goals: Mapped[list["PlanGoal"]] = sa_relationship(
        "PlanGoal",
        back_populates="plan_version",
        cascade="all, delete-orphan",
        order_by="PlanGoal.sort_order",
        lazy="selectin",
    )
    signatures: Mapped[list["PlanSignature"]] = sa_relationship(
        "PlanSignature",
        back_populates="plan_version",
        cascade="all, delete-orphan",
        order_by="PlanSignature.signed_at",
        lazy="selectin",
    )


class PlanParticipant(Base, TimestampMixin):
    """Relational participant in a plan meeting / agreement."""

    __tablename__ = "plan_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)  # WORKER, FAMILY_MEMBER, etc.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("providers.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    relationship: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    attendance_status: Mapped[str] = mapped_column(sa.String(50), default="ATTENDED", nullable=False)
    signature_required: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    # Relationships
    plan_version: Mapped["PlanVersion"] = sa_relationship("PlanVersion", back_populates="participants")
    user: Mapped["User | None"] = sa_relationship("User", foreign_keys=[user_id], lazy="selectin")
    person: Mapped["Person | None"] = sa_relationship("Person", foreign_keys=[person_id], lazy="selectin")
    provider: Mapped["Provider | None"] = sa_relationship("Provider", foreign_keys=[provider_id], lazy="selectin")


class PlanConcern(Base, TimestampMixin):
    """Harm statement, danger statement, or worry in a plan."""

    __tablename__ = "plan_concerns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concern_type: Mapped[str] = mapped_column(sa.String(50), default="SAFETY_CONCERN", nullable=False)
    statement: Mapped[str] = mapped_column(sa.Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)  # Low, Medium, High, Critical
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    plan_version: Mapped["PlanVersion"] = sa_relationship("PlanVersion", back_populates="concerns")


class PlanStrength(Base, TimestampMixin):
    """Family strength, protective capacity, or cultural support in a plan."""

    __tablename__ = "plan_strengths"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    statement: Mapped[str] = mapped_column(sa.Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    plan_version: Mapped["PlanVersion"] = sa_relationship("PlanVersion", back_populates="strengths")


class PlanGoal(Base, TimestampMixin):
    """Measurable family goal in a plan version."""

    __tablename__ = "plan_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    target_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(sa.String(50), default="NOT_STARTED", nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    plan_version: Mapped["PlanVersion"] = sa_relationship("PlanVersion", back_populates="goals")
    completer: Mapped["User | None"] = sa_relationship("User", foreign_keys=[completed_by], lazy="selectin")
    creator: Mapped["User | None"] = sa_relationship("User", foreign_keys=[created_by], lazy="selectin")

    activities: Mapped[list["PlanActivity"]] = sa_relationship(
        "PlanActivity",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="PlanActivity.sort_order",
        lazy="selectin",
    )
    progress_updates: Mapped[list["GoalProgressUpdate"]] = sa_relationship(
        "GoalProgressUpdate",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="GoalProgressUpdate.created_at.desc()",
        lazy="selectin",
    )


class PlanActivity(Base, TimestampMixin):
    """Actionable task belonging to a Goal, assigned to a worker, family member, or provider."""

    __tablename__ = "plan_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    responsible_type: Mapped[str] = mapped_column(sa.String(50), default="WORKER", nullable=False)
    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    responsible_person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    responsible_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    due_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(sa.String(50), default="NOT_STARTED", nullable=False, index=True)

    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    goal: Mapped["PlanGoal"] = sa_relationship("PlanGoal", back_populates="activities")
    responsible_user: Mapped["User | None"] = sa_relationship("User", foreign_keys=[responsible_user_id], lazy="selectin")
    responsible_person: Mapped["Person | None"] = sa_relationship("Person", foreign_keys=[responsible_person_id], lazy="selectin")


class GoalProgressUpdate(Base):
    """Progress note and status snapshot on a goal."""

    __tablename__ = "goal_progress_updates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    notes: Mapped[str] = mapped_column(sa.Text, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    goal: Mapped["PlanGoal"] = sa_relationship("PlanGoal", back_populates="progress_updates")
    updater: Mapped["User | None"] = sa_relationship("User", foreign_keys=[updated_by], lazy="selectin")


class PlanAssessment(Base):
    """Traceable link between a plan and a completed assessment."""

    __tablename__ = "plan_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(sa.String(50), default="INFORMED_BY", nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    __table_args__ = (sa.UniqueConstraint("plan_id", "assessment_id", name="uq_plan_assessment_link"),)

    plan: Mapped["Plan"] = sa_relationship("Plan", back_populates="assessments")
    assessment: Mapped["Assessment"] = sa_relationship("Assessment", foreign_keys=[assessment_id], lazy="selectin")


class PlanSignature(Base):
    """Cryptographic signature record bound to a plan version and SHA-256 document hash."""

    __tablename__ = "plan_signatures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("plan_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signer_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)  # WORKER, PARENT_GUARDIAN, CHILD_YOUTH, ELDER, PROVIDER, OTHER
    signer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    signer_person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    signer_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    signer_role: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    signature_data: Mapped[str | None] = mapped_column(sa.Text, nullable=True)  # Base64 Canvas/Vector
    signature_image_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    signed_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(sa.String(50), default="ELECTRONIC_DRAW", nullable=False)  # ELECTRONIC_DRAW, ELECTRONIC_TYPE, PHYSICAL_UPLOAD
    document_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    attestation_text: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(sa.String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    plan_version: Mapped["PlanVersion"] = sa_relationship("PlanVersion", back_populates="signatures")
    signer_user: Mapped["User | None"] = sa_relationship("User", foreign_keys=[signer_user_id], lazy="selectin")
    signer_person: Mapped["Person | None"] = sa_relationship("Person", foreign_keys=[signer_person_id], lazy="selectin")
