"""Assessment Engine domain models: templates, versions, sections, questions, answers, and instances."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.client import Client
    from app.models.family import Family
    from app.models.household import Household
    from app.models.person import Person
    from app.models.user import User


class AssessmentTemplate(Base, TimestampMixin):
    """Logical assessment type definition (e.g., HOME_ASSESSMENT, THREAT_ASSESSMENT, AIEI_ASSESSMENT)."""

    __tablename__ = "assessment_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    versions: Mapped[list[AssessmentTemplateVersion]] = relationship(
        "AssessmentTemplateVersion", back_populates="template", cascade="all, delete-orphan", lazy="selectin"
    )
    assessments: Mapped[list[Assessment]] = relationship("Assessment", back_populates="template", lazy="noload")


class AssessmentTemplateVersion(Base, TimestampMixin, SoftDeleteMixin):
    """Immutable published or draft version of an assessment questionnaire."""

    __tablename__ = "assessment_template_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")  # DRAFT, PUBLISHED, RETIRED
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    template: Mapped[AssessmentTemplate] = relationship("AssessmentTemplate", back_populates="versions")
    sections: Mapped[list[AssessmentSection]] = relationship(
        "AssessmentSection",
        back_populates="template_version",
        cascade="all, delete-orphan",
        order_by="AssessmentSection.sort_order",
        lazy="selectin",
    )
    assessments: Mapped[list[Assessment]] = relationship("Assessment", back_populates="template_version", lazy="noload")

    __table_args__ = (UniqueConstraint("template_id", "version_number", name="uq_template_version_number"),)


class AssessmentSection(Base, TimestampMixin):
    """Ordered logical section within a specific template version."""

    __tablename__ = "assessment_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_template_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visibility_condition: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    template_version: Mapped[AssessmentTemplateVersion] = relationship(
        "AssessmentTemplateVersion", back_populates="sections"
    )
    questions: Mapped[list[AssessmentQuestion]] = relationship(
        "AssessmentQuestion",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestion.sort_order",
        lazy="selectin",
    )


class AssessmentQuestion(Base, TimestampMixin):
    """Individual question within an assessment section with validation and visibility metadata."""

    __tablename__ = "assessment_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # BOOLEAN, SINGLE_SELECT, MULTI_SELECT, TEXT, LONG_TEXT, NUMBER, DATE, DATETIME, LOOKUP
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_reportable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    validation_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    visibility_condition: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    lookup_list_key: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    section: Mapped[AssessmentSection] = relationship("AssessmentSection", back_populates="questions")
    options: Mapped[list[AssessmentQuestionOption]] = relationship(
        "AssessmentQuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestionOption.sort_order",
        lazy="selectin",
    )


class AssessmentQuestionOption(Base, TimestampMixin):
    """Pre-configured selectable option for select-type questions."""

    __tablename__ = "assessment_question_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    question: Mapped[AssessmentQuestion] = relationship("AssessmentQuestion", back_populates="options")


class AssessmentSequence(Base):
    """Concurrency-safe sequence counter for human-readable assessment IDs (e.g., ASM-202608-0001)."""

    __tablename__ = "assessment_sequences"

    period: Mapped[str] = mapped_column(String(6), primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Assessment(Base, AuditMixin, SoftDeleteMixin):
    """Completed or in-progress assessment instance."""

    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="SET NULL"), nullable=True, index=True
    )
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_templates.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_template_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assessment_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFT", index=True
    )  # DRAFT, IN_PROGRESS, COMPLETED, LOCKED, CANCELLED
    determination: Mapped[str | None] = mapped_column(String(100), nullable=True)
    determination_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    conducted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    conducted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata_", JSONB, nullable=True)

    # Relationships
    case: Mapped[Case] = relationship("Case", foreign_keys=[case_id], lazy="joined")
    person: Mapped[Person | None] = relationship("Person", foreign_keys=[person_id], lazy="joined")
    client: Mapped[Client | None] = relationship("Client", foreign_keys=[client_id], lazy="joined")
    family: Mapped[Family | None] = relationship("Family", foreign_keys=[family_id], lazy="joined")
    household: Mapped[Household | None] = relationship("Household", foreign_keys=[household_id], lazy="joined")
    template: Mapped[AssessmentTemplate] = relationship("AssessmentTemplate", foreign_keys=[template_id], lazy="joined")
    template_version: Mapped[AssessmentTemplateVersion] = relationship(
        "AssessmentTemplateVersion", foreign_keys=[template_version_id], lazy="joined"
    )
    conductor: Mapped[User] = relationship("User", foreign_keys=[conducted_by], lazy="joined")
    completer: Mapped[User | None] = relationship("User", foreign_keys=[completed_by], lazy="noload")
    locker: Mapped[User | None] = relationship("User", foreign_keys=[locked_by], lazy="noload")

    answers: Mapped[list[AssessmentAnswer]] = relationship(
        "AssessmentAnswer", back_populates="assessment", cascade="all, delete-orphan", lazy="selectin"
    )
    status_history: Mapped[list[AssessmentStatusHistory]] = relationship(
        "AssessmentStatusHistory",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentStatusHistory.created_at",
        lazy="selectin",
    )
    unlock_events: Mapped[list[AssessmentUnlockEvent]] = relationship(
        "AssessmentUnlockEvent",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentUnlockEvent.unlocked_at",
        lazy="selectin",
    )


class AssessmentAnswer(Base, TimestampMixin):
    """Normalized, typed response value for an individual assessment question."""

    __tablename__ = "assessment_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_questions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    boolean_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    number_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_value: Mapped[date | None] = mapped_column(Date, nullable=True)
    datetime_value: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    json_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    assessment: Mapped[Assessment] = relationship("Assessment", back_populates="answers")
    question: Mapped[AssessmentQuestion] = relationship("AssessmentQuestion", lazy="joined")
    selected_options: Mapped[list[AssessmentAnswerOption]] = relationship(
        "AssessmentAnswerOption", back_populates="answer", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (UniqueConstraint("assessment_id", "question_id", name="uq_assessment_question_answer"),)


class AssessmentAnswerOption(Base):
    """Relational selection container for multi-select option answers."""

    __tablename__ = "assessment_answer_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_answers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_question_options.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    answer: Mapped[AssessmentAnswer] = relationship("AssessmentAnswer", back_populates="selected_options")
    option: Mapped[AssessmentQuestionOption] = relationship("AssessmentQuestionOption", lazy="joined")

    __table_args__ = (UniqueConstraint("answer_id", "option_id", name="uq_answer_option_selection"),)


class AssessmentStatusHistory(Base):
    """Audit log of assessment state transitions."""

    __tablename__ = "assessment_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    assessment: Mapped[Assessment] = relationship("Assessment", back_populates="status_history")
    author: Mapped[User] = relationship("User", lazy="joined")


class AssessmentUnlockEvent(Base):
    """Append-only audit trail of Director unlock actions on finalized assessments."""

    __tablename__ = "assessment_unlock_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unlocked_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    assessment: Mapped[Assessment] = relationship("Assessment", back_populates="unlock_events")
    director: Mapped[User] = relationship("User", lazy="joined")
