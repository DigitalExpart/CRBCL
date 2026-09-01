"""013 — Fleet Management, Trips, Maintenance, Insurance, GPS Telematics & Geofences.

Revision ID: 013_fleet_management
Revises: 012_reporting_qa
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import alembic.op as op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '013_fleet_management'
down_revision: str | None = '012_reporting_qa'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. vehicles
    op.create_table(
        'vehicles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_internal_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('make', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('licence_plate', sa.String(length=20), nullable=False, unique=True),
        sa.Column('vin', sa.String(length=50), nullable=True),
        sa.Column('vehicle_type', sa.String(length=20), nullable=False, server_default='CAR'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='AVAILABLE'),
        sa.Column('odometer_km', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('current_driver_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('insurance_expiry', sa.Date(), nullable=True),
        sa.Column('next_maintenance_date', sa.Date(), nullable=True),
        sa.Column('next_maintenance_odometer', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_vehicles_status', 'vehicles', ['status'])
    op.create_index('ix_vehicles_internal_id', 'vehicles', ['vehicle_internal_id'])

    # 2. vehicle_assignments
    op.create_table(
        'vehicle_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('driver_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('assignment_type', sa.String(length=50), nullable=False, server_default='PRIMARY'),
        sa.Column('created_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. vehicle_trips
    op.create_table(
        'vehicle_trips',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('driver_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='SET NULL'), nullable=True),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('purpose', sa.String(length=255), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('start_odometer', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('end_odometer', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('calculated_distance_km', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CHECKED_OUT'),
        sa.Column('checkout_condition', sa.String(length=50), nullable=True, server_default='GOOD'),
        sa.Column('checkin_condition', sa.String(length=50), nullable=True),
        sa.Column('has_damage_flag', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('has_maintenance_issue', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Partial unique index enforcing AT MOST ONE active CHECKED_OUT trip per vehicle
    op.create_index(
        'ix_vehicle_trips_active_checkout',
        'vehicle_trips',
        ['vehicle_id'],
        unique=True,
        postgresql_where=sa.text("status = 'CHECKED_OUT'"),
    )
    op.create_index('ix_vehicle_trips_vehicle_date', 'vehicle_trips', ['vehicle_id', 'start_time'])
    op.create_index('ix_vehicle_trips_driver_date', 'vehicle_trips', ['driver_id', 'start_time'])

    # 4. vehicle_maintenance
    op.create_table(
        'vehicle_maintenance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('maintenance_type', sa.String(length=50), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('scheduled_odometer', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('completed_odometer', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('provider_name', sa.String(length=255), nullable=True),
        sa.Column('cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SCHEDULED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_vehicle_maintenance_due', 'vehicle_maintenance', ['vehicle_id', 'status', 'scheduled_date'])

    # 5. vehicle_insurance_policies
    op.create_table(
        'vehicle_insurance_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_name', sa.String(length=255), nullable=False),
        sa.Column('policy_number', sa.String(length=100), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('coverage_details', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_vehicle_insurance_expiry', 'vehicle_insurance_policies', ['vehicle_id', 'expiry_date'])

    # 6. vehicle_locations
    op.create_table(
        'vehicle_locations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=30), nullable=False, server_default='MANUAL'),
        sa.Column('accuracy_meters', sa.Float(), nullable=True),
        sa.Column('speed_kmh', sa.Float(), nullable=True),
        sa.Column('heading_degrees', sa.Float(), nullable=True),
        sa.Column('provider_event_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_vehicle_locations_vehicle_recorded', 'vehicle_locations', ['vehicle_id', 'recorded_at'])
    op.create_index(
        'uq_vehicle_locations_provider_event',
        'vehicle_locations',
        ['vehicle_id', 'provider_event_id'],
        unique=True,
        postgresql_where=sa.text("provider_event_id IS NOT NULL"),
    )

    # 7. vehicle_telematics_links
    op.create_table(
        'vehicle_telematics_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('external_vehicle_id', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 8. fleet_geofences
    op.create_table(
        'fleet_geofences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('geofence_type', sa.String(length=50), nullable=False, server_default='SERVICE_AREA'),
        sa.Column('center_latitude', sa.Float(), nullable=True),
        sa.Column('center_longitude', sa.Float(), nullable=True),
        sa.Column('radius_meters', sa.Float(), nullable=True),
        sa.Column('polygon_geojson', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 9. fleet_geofence_events
    op.create_table(
        'fleet_geofence_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('geofence_id', UUID(as_uuid=True), sa.ForeignKey('fleet_geofences.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vehicle_id', UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=20), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('fleet_geofence_events')
    op.drop_table('fleet_geofences')
    op.drop_table('vehicle_telematics_links')
    op.drop_table('vehicle_locations')
    op.drop_table('vehicle_insurance_policies')
    op.drop_table('vehicle_maintenance')
    op.drop_table('vehicle_trips')
    op.drop_table('vehicle_assignments')
    op.drop_table('vehicles')
