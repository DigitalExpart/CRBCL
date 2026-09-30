"""SQLAlchemy models for Office Coordinator and Facility/Operations workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.fleet import Vehicle
    from app.models.user import User


class OperationsRequest(Base, TimestampMixin):
    """Centralized operational request / ticket queue."""

    __tablename__ = "operations_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="GENERAL", index=True
    )  # FACILITIES, FLEET, SUPPLIES, IT_SUPPORT, GENERAL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MEDIUM", index=True
    )  # LOW, MEDIUM, HIGH, URGENT
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="OPEN", index=True
    )  # OPEN, IN_PROGRESS, PENDING_APPROVAL, COMPLETED, CANCELLED
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requester: Mapped[User] = relationship("User", foreign_keys=[requester_id], lazy="joined")
    assigned_to: Mapped[User | None] = relationship("User", foreign_keys=[assigned_to_id], lazy="joined")


class VehicleReservation(Base, TimestampMixin):
    """Advance vehicle reservation with conflict detection."""

    __tablename__ = "vehicle_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reserved_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    passengers_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="CONFIRMED", index=True
    )  # PENDING, CONFIRMED, CHECKED_OUT, COMPLETED, CANCELLED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    vehicle: Mapped[Vehicle] = relationship("Vehicle", lazy="joined")
    reserved_by: Mapped[User] = relationship("User", foreign_keys=[reserved_by_id], lazy="joined")


class VehicleKeyLog(Base, TimestampMixin):
    """Key pickup / return custody accountability log."""

    __tablename__ = "vehicle_key_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    checked_out_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False
    )
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="CHECKED_OUT", index=True
    )  # CHECKED_OUT, RETURNED, OVERDUE
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    vehicle: Mapped[Vehicle] = relationship("Vehicle", lazy="joined")
    staff: Mapped[User] = relationship("User", foreign_keys=[staff_id], lazy="joined")
    issued_by: Mapped[User | None] = relationship("User", foreign_keys=[issued_by_id], lazy="joined")


class RoomBooking(Base, TimestampMixin):
    """Room and meeting resource reservations."""

    __tablename__ = "room_bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    booked_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    attendees_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="CONFIRMED", index=True
    )  # CONFIRMED, CANCELLED, COMPLETED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    booked_by: Mapped[User] = relationship("User", foreign_keys=[booked_by_id], lazy="joined")


class SupplyItem(Base, TimestampMixin):
    """Office and facilities supplies inventory."""

    __tablename__ = "supply_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="OFFICE", index=True
    )  # OFFICE, CLEANING, FIRST_AID, EVENT, OTHER
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="units")
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="IN_STOCK", index=True
    )  # IN_STOCK, LOW_STOCK, OUT_OF_STOCK
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
