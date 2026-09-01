"""Manual Telematics Provider handling browser/manual coordinate logging."""

from datetime import datetime

from app.services.telematics.base import (
    TelematicsEvent,
    TelematicsLocation,
    TelematicsProvider,
    TelematicsTrip,
    TelematicsVehicle,
)


class ManualProvider(TelematicsProvider):
    """Provider for action-triggered manual or browser geolocation submissions."""

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
            latitude=float(raw_payload["latitude"]),
            longitude=float(raw_payload["longitude"]),
            recorded_at=raw_payload.get("recorded_at", datetime.utcnow()),
            source="MANUAL",
            accuracy_meters=raw_payload.get("accuracy_meters"),
            provider_event_id=raw_payload.get("provider_event_id"),
        )
