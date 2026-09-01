"""Abstract Telematics Provider Base Class & Data Models (Phase 12)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TelematicsLocation:
    """Normalized GPS location telemetry ping."""

    latitude: float
    longitude: float
    recorded_at: datetime
    source: str = "TELEMATICS"
    accuracy_meters: float | None = None
    speed_kmh: float | None = None
    heading_degrees: float | None = None
    provider_event_id: str | None = None


@dataclass
class TelematicsVehicle:
    """External telematics provider vehicle representation."""

    external_vehicle_id: str
    name: str
    licence_plate: str | None = None
    vin: str | None = None
    make: str | None = None
    model: str | None = None


@dataclass
class TelematicsTrip:
    """External telematics provider completed trip summary."""

    external_trip_id: str
    external_vehicle_id: str
    start_time: datetime
    end_time: datetime
    distance_km: float
    start_odometer_km: float
    end_odometer_km: float


@dataclass
class TelematicsEvent:
    """External telematics engine event notification (geofence, engine diagnostic, panic)."""

    event_type: str
    external_vehicle_id: str
    recorded_at: datetime
    latitude: float
    longitude: float
    details: dict | None = None


class TelematicsProvider(ABC):
    """Abstract Base Class defining required operations for Telematics integrations."""

    @abstractmethod
    async def get_vehicles(self) -> list[TelematicsVehicle]:
        """Fetch list of registered vehicles from telematics provider."""
        pass

    @abstractmethod
    async def get_latest_location(self, external_vehicle_id: str) -> TelematicsLocation | None:
        """Fetch real-time last known location ping for a vehicle."""
        pass

    @abstractmethod
    async def get_locations(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsLocation]:
        """Fetch historical location breadcrumbs for a date range."""
        pass

    @abstractmethod
    async def get_trips(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsTrip]:
        """Fetch historical trips recorded by provider."""
        pass

    @abstractmethod
    async def get_events(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsEvent]:
        """Fetch telematics events recorded by provider."""
        pass

    @abstractmethod
    def normalize_location(self, raw_payload: dict) -> TelematicsLocation:
        """Normalize vendor-specific API response payload into standard TelematicsLocation."""
        pass
