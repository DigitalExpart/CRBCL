"""Migration Ledger model for tracking legacy data migration idempotency and reconciliation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MigrationLedger(Base):
    """Tracks historical entity migrations from legacy systems (Base44, RedMane, CSV, etc.)."""

    __tablename__ = "migration_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CLIENT, CASE, NOTE, DOCUMENT
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="COMPLETED", nullable=False
    )  # COMPLETED, FAILED, SKIPPED, MERGED
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_system", "target_entity_type", "source_id", name="uq_migration_ledger_source"),
    )
