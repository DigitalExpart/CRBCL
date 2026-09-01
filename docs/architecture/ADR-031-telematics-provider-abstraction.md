# ADR-031: Telematics Provider Abstraction Layer

## Status
Approved

## Context
CRBCL vehicles may utilize third-party telematics hardware and software services (e.g., Samsara, Easy Fleet, Geotab) in the future to continuously monitor GPS location, diagnostics, and telematics events. Directly coupling backend fleet logic to a specific vendor API creates vendor lock-in, increases testing complexity, and breaks offline/manual fallback modes.

## Decision

### 1. Abstract Telematics Interface
We introduce an abstract provider interface `TelematicsProvider` in `backend/app/services/telematics/base.py`:

```python
class TelematicsProvider(ABC):
    @abstractmethod
    async def get_vehicles(self) -> list[TelematicsVehicle]:
        pass

    @abstractmethod
    async def get_latest_location(self, external_vehicle_id: str) -> TelematicsLocation | None:
        pass

    @abstractmethod
    async def get_locations(self, external_vehicle_id: str, start_time: datetime, end_time: datetime) -> list[TelematicsLocation]:
        pass

    @abstractmethod
    async def get_trips(self, external_vehicle_id: str, start_time: datetime, end_time: datetime) -> list[TelematicsTrip]:
        pass

    @abstractmethod
    async def get_events(self, external_vehicle_id: str, start_time: datetime, end_time: datetime) -> list[TelematicsEvent]:
        pass

    @abstractmethod
    def normalize_location(self, raw_payload: dict) -> TelematicsLocation:
        pass
```

### 2. Provider Implementations
- **`ManualProvider`**: Default provider handling manual GPS check-in points and browser geolocation submissions.
- **`FakeProvider`**: Deterministic mock provider producing synthetic GPS feeds for automated testing and development.
- **`SamsaraProvider` (Skeleton)**: Future integration adapter translating Samsara API v2 JSON endpoints to standard `TelematicsLocation` dataclasses.
- **`EasyFleetProvider` (Skeleton)**: Future integration adapter for Easy Fleet telematics services.

### 3. Provider Isolation & Fail-Safe Invariants
- Domain logic (`FleetService`) interacts exclusively with `TelematicsProvider` methods.
- Telematics API failures, network timeouts, or rate limits are caught, logged, and isolated within outbox sync tasks.
- Telematics failures **never** block manual vehicle check-out, check-in, or routine fleet management operations.

## Consequences
- Complete independence from live paid telematics credentials during Phase 12 development and automated testing.
- Plug-and-play architecture for future Samsara or Easy Fleet deployment.
