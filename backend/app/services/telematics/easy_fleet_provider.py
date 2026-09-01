"""Easy Fleet Telematics Provider Adapter Skeleton (Phase 12)."""

from datetime import datetime

from app.services.telematics.base import (
    TelematicsEvent,
    TelematicsLocation,
    TelematicsProvider,
    TelematicsTrip,
    TelematicsVehicle,
)


class EasyFleetProvider(TelematicsProvider):
    """Adapter skeleton for future Easy Fleet telematics integration."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def get_vehicles(self) -> list[TelematicsVehicle]:
        return []

    async def get_latest_location(self, external_vehicle_id: str) -> TelematicsLocation | None:
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
        return TelematicsLocation(
            latitude=float(raw_payload.get("lat", 0.0)),
            longitude=float(raw_payload.get("lng", 0.0)),
            recorded_at=datetime.utcnow(),
            source="TELEMATICS",
            provider_event_id=raw_payload.get("event_id"),
        )
