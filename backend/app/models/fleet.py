"""Fleet Management SQLAlchemy Models for CRBCL (Phase 12)."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Vehicle(Base):
    """Primary vehicle asset record."""

    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_internal_id = Column(String(50), unique=True, nullable=False)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    licence_plate = Column(String(20), unique=True, nullable=False)
    vin = Column(String(50), nullable=True)
    vehicle_type = Column(String(20), nullable=False, default="CAR")  # CAR, VAN, TRUCK, SUV, OTHER
    status = Column(
        String(20), nullable=False, default="AVAILABLE"
    )  # AVAILABLE, IN_USE, MAINTENANCE, OUT_OF_SERVICE, RETIRED
    odometer_km = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    current_driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    next_maintenance_odometer = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    current_driver = relationship("User", foreign_keys=[current_driver_id])
    trips = relationship("VehicleTrip", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_records = relationship("VehicleMaintenance", back_populates="vehicle", cascade="all, delete-orphan")
    insurance_policies = relationship("VehicleInsurancePolicy", back_populates="vehicle", cascade="all, delete-orphan")
    locations = relationship("VehicleLocation", back_populates="vehicle", cascade="all, delete-orphan")
    assignments = relationship("VehicleAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    telematics_links = relationship("VehicleTelematicsLink", back_populates="vehicle", cascade="all, delete-orphan")


class VehicleAssignment(Base):
    """Persistent or long-term vehicle driver assignment."""

    __tablename__ = "vehicle_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    assignment_type = Column(String(50), nullable=False, default="PRIMARY")
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="assignments")
    driver = relationship("User", foreign_keys=[driver_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class VehicleTrip(Base):
    """Vehicle check-out / check-in operational trip record."""

    __tablename__ = "vehicle_trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)

    purpose = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    start_odometer = Column(Numeric(10, 2), nullable=False)
    end_odometer = Column(Numeric(10, 2), nullable=True)
    calculated_distance_km = Column(Numeric(10, 2), nullable=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="CHECKED_OUT")  # PLANNED, CHECKED_OUT, CHECKED_IN, CANCELLED

    checkout_condition = Column(String(50), nullable=True, default="GOOD")
    checkin_condition = Column(String(50), nullable=True)
    has_damage_flag = Column(Boolean, default=False, nullable=False)
    has_maintenance_issue = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("User", foreign_keys=[driver_id])
    case = relationship("Case", foreign_keys=[case_id])
    client = relationship("Client", foreign_keys=[client_id])


class VehicleMaintenance(Base):
    """Vehicle preventive and corrective maintenance record."""

    __tablename__ = "vehicle_maintenance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    maintenance_type = Column(
        String(50), nullable=False
    )  # OIL_CHANGE, TIRE_SERVICE, BRAKES, INSPECTION, REPAIR, RECALL, OTHER
    scheduled_date = Column(Date, nullable=True)
    scheduled_odometer = Column(Numeric(10, 2), nullable=True)
    completed_date = Column(Date, nullable=True)
    completed_odometer = Column(Numeric(10, 2), nullable=True)
    provider_name = Column(String(255), nullable=True)
    cost = Column(Numeric(10, 2), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(
        String(20), nullable=False, default="SCHEDULED"
    )  # SCHEDULED, DUE, IN_PROGRESS, COMPLETED, CANCELLED
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")


class VehicleInsurancePolicy(Base):
    """Vehicle insurance policy and renewal history."""

    __tablename__ = "vehicle_insurance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(255), nullable=False)
    policy_number = Column(String(100), nullable=False)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE, EXPIRED, CANCELLED, RENEWED
    coverage_details = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="insurance_policies")


class VehicleLocation(Base):
    """GPS location ping for vehicle position tracking."""

    __tablename__ = "vehicle_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(30), nullable=False, default="MANUAL")  # MANUAL, MOBILE, TELEMATICS
    accuracy_meters = Column(Float, nullable=True)
    speed_kmh = Column(Float, nullable=True)
    heading_degrees = Column(Float, nullable=True)
    provider_event_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="locations")


class VehicleTelematicsLink(Base):
    """Telematics vendor binding for vehicle hardware tracking."""

    __tablename__ = "vehicle_telematics_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(50), nullable=False)  # SAMSARA, EASY_FLEET, FAKE
    external_vehicle_id = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="telematics_links")


class FleetGeofence(Base):
    """Geofence boundary area definition."""

    __tablename__ = "fleet_geofences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    geofence_type = Column(String(50), nullable=False, default="SERVICE_AREA")
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    radius_meters = Column(Float, nullable=True)
    polygon_geojson = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    events = relationship("FleetGeofenceEvent", back_populates="geofence", cascade="all, delete-orphan")


class FleetGeofenceEvent(Base):
    """Geofence boundary transition event log."""

    __tablename__ = "fleet_geofence_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    geofence_id = Column(UUID(as_uuid=True), ForeignKey("fleet_geofences.id", ondelete="CASCADE"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(20), nullable=False)  # ENTER, EXIT
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    geofence = relationship("FleetGeofence", back_populates="events")
    vehicle = relationship("Vehicle")
