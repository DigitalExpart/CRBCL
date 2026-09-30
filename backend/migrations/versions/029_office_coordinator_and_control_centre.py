"""Add Office Coordinator operational tables and master dashboard control foundation.

Revision ID: 029_office_coordinator_and_control_centre
Revises: 028_client_approval_workflow
Create Date: 2026-09-30 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "029_office_coordinator_and_control_centre"
down_revision: str | None = "028_client_approval_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Create operations_requests table ───────────────────────
    op.create_table(
        "operations_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_number", sa.String(50), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=False, server_default="GENERAL"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column(
            "requester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_to_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_operations_requests_req_num", "operations_requests", ["request_number"])
    op.create_index("ix_operations_requests_category", "operations_requests", ["category"])
    op.create_index("ix_operations_requests_priority", "operations_requests", ["priority"])
    op.create_index("ix_operations_requests_status", "operations_requests", ["status"])
    op.create_index("ix_operations_requests_requester_id", "operations_requests", ["requester_id"])

    # ── 2. Create vehicle_reservations table ──────────────────────
    op.create_table(
        "vehicle_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reserved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("destination", sa.String(255), nullable=True),
        sa.Column("passengers_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(30), nullable=False, server_default="CONFIRMED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicle_reservations_vehicle_id", "vehicle_reservations", ["vehicle_id"])
    op.create_index("ix_vehicle_reservations_start_time", "vehicle_reservations", ["start_time"])
    op.create_index("ix_vehicle_reservations_end_time", "vehicle_reservations", ["end_time"])
    op.create_index("ix_vehicle_reservations_status", "vehicle_reservations", ["status"])

    # ── 3. Create vehicle_key_logs table ──────────────────────────
    op.create_table(
        "vehicle_key_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key_tag", sa.String(50), nullable=False),
        sa.Column(
            "staff_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "issued_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="CHECKED_OUT"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicle_key_logs_vehicle_id", "vehicle_key_logs", ["vehicle_id"])
    op.create_index("ix_vehicle_key_logs_key_tag", "vehicle_key_logs", ["key_tag"])
    op.create_index("ix_vehicle_key_logs_staff_id", "vehicle_key_logs", ["staff_id"])
    op.create_index("ix_vehicle_key_logs_status", "vehicle_key_logs", ["status"])

    # ── 4. Create room_bookings table ─────────────────────────────
    op.create_table(
        "room_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("room_name", sa.String(100), nullable=False),
        sa.Column(
            "booked_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attendees_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(30), nullable=False, server_default="CONFIRMED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_room_bookings_room_name", "room_bookings", ["room_name"])
    op.create_index("ix_room_bookings_start_time", "room_bookings", ["start_time"])
    op.create_index("ix_room_bookings_end_time", "room_bookings", ["end_time"])
    op.create_index("ix_room_bookings_status", "room_bookings", ["status"])

    # ── 5. Create supply_items table ──────────────────────────────
    op.create_table(
        "supply_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="OFFICE"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(50), nullable=False, server_default="units"),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("reorder_threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.String(30), nullable=False, server_default="IN_STOCK"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_supply_items_item_name", "supply_items", ["item_name"])
    op.create_index("ix_supply_items_category", "supply_items", ["category"])
    op.create_index("ix_supply_items_status", "supply_items", ["status"])


def downgrade() -> None:
    op.drop_table("supply_items")
    op.drop_table("room_bookings")
    op.drop_table("vehicle_key_logs")
    op.drop_table("vehicle_reservations")
    op.drop_table("operations_requests")
