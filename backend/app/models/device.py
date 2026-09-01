"""Mobile Device model for registration, status tracking, and remote revocation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MobileDevice(Base):
    """Tracks registered field caseworker mobile devices for offline sync authorization and revocation."""

    __tablename__ = "mobile_devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Caseworker Handheld")
    os_type: Mapped[str] = mapped_column(String(20), nullable=False, default="Android")  # Android, iOS
    app_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    device_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, REVOKED, WIPED
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id], lazy="joined")

    __table_args__ = (Index("ix_mobile_devices_user_status", "user_id", "device_status"),)
