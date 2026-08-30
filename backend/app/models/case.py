"""Case model."""

from __future__ import annotations

import uuid

from sqlalchemy import Date, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class Case(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    case_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Open", nullable=False)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    intake_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    target_resolution_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    closed_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    service_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships via UUIDs
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    family_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_worker_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    assigned_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_priority", "priority"),
    )
