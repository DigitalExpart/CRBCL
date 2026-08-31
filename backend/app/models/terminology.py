"""Terminology keys and translations."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class TerminologyKey(Base, TimestampMixin):
    __tablename__ = "terminology_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    context: Mapped[str] = mapped_column(String(100), default="general", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    translations: Mapped[list[TerminologyTranslation]] = relationship(
        "TerminologyTranslation", back_populates="terminology_key", lazy="selectin"
    )


class TerminologyTranslation(Base, TimestampMixin):
    __tablename__ = "terminology_translations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("terminology_keys.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    value: Mapped[str] = mapped_column(Text, nullable=False)
    is_approved: Mapped[bool] = mapped_column(default=False, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    terminology_key: Mapped[TerminologyKey] = relationship("TerminologyKey", back_populates="translations")
