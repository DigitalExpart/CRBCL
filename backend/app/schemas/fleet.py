"""Fleet Pydantic Schemas for API requests and responses (Phase 12)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── 1. Vehicle Schemas ───────────────────────────────────────────
class VehicleCreate(BaseModel):
    vehicle_internal_id: str = Field(..., max_length=50)
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    year: int = Field(..., ge=1900, le=2100)
    licence_plate: str = Field(..., max_length=20)
    vin: str | None = Field(None, max_length=50)
    vehicle_type: str = Field("CAR", max_length=20)  # CAR, VAN, TRUCK, SUV, OTHER
    status: str = Field("AVAILABLE", max_length=20)  # AVAILABLE, IN_USE, MAINTENANCE, OUT_OF_SERVICE, RETIRED
    odometer_km: Decimal = Field(Decimal("0.00"), ge=0)
    notes: str | None = None


class VehicleUpdate(BaseModel):
    make: str | None = None
    model: str | None = None
    year: int | None = None
    licence_plate: str | None = None
    vehicle_type: str | None = None
    status: str | None = None
    odometer_km: Decimal | None = None
    notes: str | None = None


class VehicleResponse(BaseModel):
    id: uuid.UUID
    vehicle_internal_id: str
    make: str
    model: str
    year: int
    licence_plate: str
    vin: str | None = None
    vehicle_type: str
    status: str
    odometer_km: Decimal
    current_driver_id: uuid.UUID | None = None
    insurance_expiry: date | None = None
    next_maintenance_date: date | None = None
    next_maintenance_odometer: Decimal | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

    class Config:
        from_attributes = True


# ── 2. Trip Schemas ──────────────────────────────────────────────
class TripCheckoutRequest(BaseModel):
    driver_id: uuid.UUID
    case_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    purpose: str = Field(..., max_length=255)
    destination: str = Field(..., max_length=255)
    start_odometer: Decimal = Field(..., ge=0)
    start_time: datetime | None = None
    checkout_condition: str = Field("GOOD", max_length=50)
    notes: str | None = None


class TripCheckinRequest(BaseModel):
    end_odometer: Decimal = Field(..., ge=0)
    end_time: datetime | None = None
    checkin_condition: str = Field("GOOD", max_length=50)
    has_damage_flag: bool = False
    has_maintenance_issue: bool = False
    notes: str | None = None


class TripResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    case_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    purpose: str
    destination: str
    start_odometer: Decimal
    end_odometer: Decimal | None = None
    calculated_distance_km: Decimal | None = None
    start_time: datetime
    end_time: datetime | None = None
    status: str
    checkout_condition: str | None = None
    checkin_condition: str | None = None
    has_damage_flag: bool
    has_maintenance_issue: bool
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 3. Maintenance Schemas ───────────────────────────────────────
class MaintenanceCreate(BaseModel):
    vehicle_id: uuid.UUID
    maintenance_type: str = Field(..., max_length=50)
    scheduled_date: date | None = None
    scheduled_odometer: Decimal | None = None
    provider_name: str | None = Field(None, max_length=255)
    description: str
    notes: str | None = None


class MaintenanceCompleteRequest(BaseModel):
    completed_date: date | None = None
    completed_odometer: Decimal | None = None
    cost: Decimal | None = None
    notes: str | None = None


class MaintenanceResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    maintenance_type: str
    scheduled_date: date | None = None
    scheduled_odometer: Decimal | None = None
    completed_date: date | None = None
    completed_odometer: Decimal | None = None
    provider_name: str | None = None
    cost: Decimal | None = None
    description: str
    status: str
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 4. Insurance Schemas ─────────────────────────────────────────
class InsuranceCreate(BaseModel):
    vehicle_id: uuid.UUID
    provider_name: str = Field(..., max_length=255)
    policy_number: str = Field(..., max_length=100)
    effective_date: date
    expiry_date: date
    coverage_details: str | None = None
    notes: str | None = None


class InsuranceResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    provider_name: str
    policy_number: str
    effective_date: date
    expiry_date: date
    status: str
    coverage_details: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 5. Location & Geofence Schemas ──────────────────────────────
class LocationRecordRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    recorded_at: datetime | None = None
    source: str = Field("MANUAL", max_length=30)
    accuracy_meters: float | None = None
    speed_kmh: float | None = None
    heading_degrees: float | None = None
    provider_event_id: str | None = None


class LocationResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    latitude: float
    longitude: float
    recorded_at: datetime
    source: str
    accuracy_meters: float | None = None
    speed_kmh: float | None = None
    heading_degrees: float | None = None
    provider_event_id: str | None = None

    class Config:
        from_attributes = True


class GeofenceCreate(BaseModel):
    name: str = Field(..., max_length=100)
    geofence_type: str = Field("SERVICE_AREA", max_length=50)
    center_latitude: float | None = None
    center_longitude: float | None = None
    radius_meters: float | None = None
    polygon_geojson: str | None = None


class GeofenceResponse(BaseModel):
    id: uuid.UUID
    name: str
    geofence_type: str
    center_latitude: float | None = None
    center_longitude: float | None = None
    radius_meters: float | None = None
    polygon_geojson: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
