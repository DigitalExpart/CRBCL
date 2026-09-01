"""Samsara Telematics Provider Adapter Skeleton (Phase 12)."""

from datetime import datetime

from app.services.telematics.base import (
    TelematicsEvent,
    TelematicsLocation,
    TelematicsProvider,
    TelematicsTrip,
    TelematicsVehicle,
)


class SamsaraProvider(TelematicsProvider):
    """Adapter skeleton for future Samsara API v2 integration."""

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token

    async def get_vehicles(self) -> list[TelematicsVehicle]:
        # Future Samsara GET /fleet/vehicles integration
        return []

    async def get_latest_location(self, external_vehicle_id: str) -> TelematicsLocation | None:
        # Future Samsara GET /fleet/vehicles/locations integration
        return None

    async def get_locations(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsLocation]:
        return []

    async def get_trips(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsTrip]:
        return []

    async def get_events(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsEvent]:
        return []

    def normalize_location(self, raw_payload: dict) -> TelematicsLocation:
        # Samsara payload normalization logic
        location_data = raw_payload.get("location", {})
        return TelematicsLocation(
            latitude=float(location_data.get("latitude", 0.0)),
            longitude=float(location_data.get("longitude", 0.0)),
            recorded_at=datetime.fromisoformat(raw_payload.get("time")),
            source="TELEMATICS",
            accuracy_meters=location_data.get("accuracy"),
            speed_kmh=location_data.get("speedMilesPerHour", 0.0) * 1.60934,
            provider_event_id=raw_payload.get("id"),
        )
