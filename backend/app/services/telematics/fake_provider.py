"""Fake Telematics Provider generating synthetic feeds for testing/offline dev."""

from datetime import datetime

from app.services.telematics.base import (
    TelematicsEvent,
    TelematicsLocation,
    TelematicsProvider,
    TelematicsTrip,
    TelematicsVehicle,
)


class FakeProvider(TelematicsProvider):
    """Synthetic provider returning deterministic GPS coordinates (Regina/Cowessess SK area)."""

    def __init__(self, fail_mode: bool = False):
        self.fail_mode = fail_mode

    async def get_vehicles(self) -> list[TelematicsVehicle]:
        if self.fail_mode:
            raise ConnectionError("Simulated telematics connection failure")
        return [
            TelematicsVehicle(
                external_vehicle_id="fake-v-101",
                name="Van 101",
                licence_plate="SK-CRB-101",
                make="Dodge",
                model="Caravan",
            ),
            TelematicsVehicle(
                external_vehicle_id="fake-v-102",
                name="SUV 102",
                licence_plate="SK-CRB-102",
                make="Ford",
                model="Explorer",
            ),
        ]

    async def get_latest_location(self, external_vehicle_id: str) -> TelematicsLocation | None:
        if self.fail_mode:
            raise ConnectionError("Simulated telematics connection failure")
        # Default coordinates near Regina / Cowessess, SK
        return TelematicsLocation(
            latitude=50.4452,
            longitude=-104.6189,
            recorded_at=datetime.utcnow(),
            source="TELEMATICS",
            accuracy_meters=5.0,
            speed_kmh=45.0,
            heading_degrees=180.0,
            provider_event_id=f"evt-{external_vehicle_id}-latest",
        )

    async def get_locations(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsLocation]:
        if self.fail_mode:
            raise ConnectionError("Simulated telematics connection failure")
        return [
            TelematicsLocation(
                latitude=50.4452,
                longitude=-104.6189,
                recorded_at=start_time,
                source="TELEMATICS",
                provider_event_id=f"evt-{external_vehicle_id}-1",
            ),
            TelematicsLocation(
                latitude=50.4500,
                longitude=-104.6200,
                recorded_at=end_time,
                source="TELEMATICS",
                provider_event_id=f"evt-{external_vehicle_id}-2",
            ),
        ]

    async def get_trips(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsTrip]:
        if self.fail_mode:
            raise ConnectionError("Simulated telematics connection failure")
        return [
            TelematicsTrip(
                external_trip_id="fake-trip-999",
                external_vehicle_id=external_vehicle_id,
                start_time=start_time,
                end_time=end_time,
                distance_km=25.4,
                start_odometer_km=10000.0,
                end_odometer_km=10025.4,
            )
        ]

    async def get_events(
        self, external_vehicle_id: str, start_time: datetime, end_time: datetime
    ) -> list[TelematicsEvent]:
        if self.fail_mode:
            raise ConnectionError("Simulated telematics connection failure")
        return []

    def normalize_location(self, raw_payload: dict) -> TelematicsLocation:
        return TelematicsLocation(
            latitude=float(raw_payload.get("lat", 50.4452)),
            longitude=float(raw_payload.get("lng", -104.6189)),
            recorded_at=datetime.utcnow(),
            source="TELEMATICS",
            provider_event_id=raw_payload.get("id"),
        )
