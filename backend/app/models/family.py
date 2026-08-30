"""Family model."""

from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class Family(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "families"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_name: Mapped[str] = mapped_column(String(300), nullable=False)
    primary_contact_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    primary_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primary_contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(200), nullable=True)
    province: Mapped[str] = mapped_column(String(100), default="Saskatchewan", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="Low", nullable=False)
    indigenous_identity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    band_nation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    total_members: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
