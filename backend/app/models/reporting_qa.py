"""Reporting, Quality Assurance, Audit Tickler, Passports & Dashboard Models (Phase 11)."""

import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SavedReport(Base):
    """Saved report configuration created by users."""

    __tablename__ = "saved_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_key = Column(String(100), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    visibility = Column(String(50), nullable=False, default="PRIVATE")  # PRIVATE, TEAM, AUTHORIZED_SHARED
    configuration = Column(JSONB, nullable=False, default=dict)

    # Audit & Soft Delete
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_user_id])
    team = relationship("Team", foreign_keys=[team_id])
    runs = relationship("ReportRun", back_populates="saved_report", cascade="all, delete-orphan")


class ReportRun(Base):
    """Execution history log for reports and exports."""

    __tablename__ = "report_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saved_report_id = Column(
        UUID(as_uuid=True), ForeignKey("saved_reports.id", ondelete="SET NULL"), nullable=True, index=True
    )
    run_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="RUNNING")  # RUNNING, SUCCESS, FAILED
    row_count = Column(Integer, nullable=False, default=0)
    export_format = Column(String(20), nullable=True)  # JSON, CSV, XLSX, PDF
    parameters_snapshot = Column(JSONB, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    # Relationships
    saved_report = relationship("SavedReport", back_populates="runs")
    runner = relationship("User", foreign_keys=[run_by_id])


class QAAuditTemplate(Base):
    """Quality Assurance Audit Template configuration."""

    __tablename__ = "qa_audit_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cadence = Column(String(50), nullable=False, default="QUARTERLY")  # MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL
    target_case_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit & Soft Delete
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    versions = relationship("QAAuditTemplateVersion", back_populates="template", cascade="all, delete-orphan")


class QAAuditTemplateVersion(Base):
    """Immutable version of a QA checklist template."""

    __tablename__ = "qa_audit_template_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("qa_audit_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    published_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    published_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_notes = Column(Text, nullable=True)

    # Relationships
    template = relationship("QAAuditTemplate", back_populates="versions")
    items = relationship("QAAuditTemplateItem", back_populates="version_obj", cascade="all, delete-orphan")


class QAAuditTemplateItem(Base):
    """Checklist item in a QA template version."""

    __tablename__ = "qa_audit_template_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(
        UUID(as_uuid=True), ForeignKey("qa_audit_template_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section = Column(String(100), nullable=False, default="General Documentation")
    item_text = Column(String(500), nullable=False)
    guidance_notes = Column(Text, nullable=True)
    severity = Column(String(50), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    sort_order = Column(Integer, nullable=False, default=0)
    is_required = Column(Boolean, nullable=False, default=True)

    # Relationships
    version_obj = relationship("QAAuditTemplateVersion", back_populates="items")


class QAAudit(Base):
    """Case Quality Assurance Audit Instance."""

    __tablename__ = "qa_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    template_version_id = Column(
        UUID(as_uuid=True), ForeignKey("qa_audit_template_versions.id", ondelete="RESTRICT"), nullable=False
    )
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    review_date = Column(Date, nullable=False, default=date.today)
    status = Column(String(50), nullable=False, default="DRAFT", index=True)  # DRAFT, IN_PROGRESS, COMPLETED
    overall_score = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Audit & Soft Delete
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    case = relationship("Case", foreign_keys=[case_id])
    template_version = relationship("QAAuditTemplateVersion", foreign_keys=[template_version_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    results = relationship("QAAuditResult", back_populates="audit", cascade="all, delete-orphan")


class QAAuditResult(Base):
    """Specific response to a QA checklist item."""

    __tablename__ = "qa_audit_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("qa_audits.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("qa_audit_template_items.id", ondelete="RESTRICT"), nullable=False)
    compliance = Column(String(20), nullable=False, default="YES")  # YES, NO, NA
    notes = Column(Text, nullable=True)
    finding_severity = Column(String(50), nullable=True)
    followup_required = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    audit = relationship("QAAudit", back_populates="results")
    item = relationship("QAAuditTemplateItem", foreign_keys=[item_id])


class DashboardWidget(Base):
    """Server-registered operational metric dashboard widget."""

    __tablename__ = "dashboard_widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    widget_key = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default="OPERATIONAL")
    required_permission = Column(String(100), nullable=True)
    default_width = Column(Integer, nullable=False, default=1)
    default_height = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserDashboardWidget(Base):
    """Per-user dashboard widget position, size, and visibility preferences."""

    __tablename__ = "user_dashboard_widgets"
    __table_args__ = (UniqueConstraint("user_id", "widget_key", name="uq_user_dashboard_widget"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    widget_key = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=1)
    height = Column(Integer, nullable=False, default=1)
    is_visible = Column(Boolean, nullable=False, default=True)
    settings = Column(JSONB, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
