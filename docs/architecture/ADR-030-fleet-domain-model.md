# ADR-030: Fleet Management & Vehicle Operations Domain Model

## Status
Approved

## Context
Chief Red Bear Children's Lodge (CRBCL) operates a fleet of service vehicles (cars, vans, SUVs, trucks) used by caseworkers and transportation staff to transport children and families, conduct home visits, deliver supplies, and carry out agency operations. To maintain strict financial accountability, worker safety, asset protection, and operational efficiency, CRBCL requires a comprehensive Fleet Management domain.

## Decision

### 1. Core Fleet Entities
We establish the following domain entities in `backend/app/models/fleet.py`:

1. **Vehicle (`vehicles`)**:
   - Primary asset registry (`id`, `vehicle_internal_id`, `make`, `model`, `year`, `licence_plate`, `vin`, `vehicle_type`, `status`, `odometer_km`, `current_driver_id`, `insurance_expiry`, `next_maintenance_date`, `notes`, `created_at`, `updated_at`, `archived_at`).
   - Vehicle Types: `CAR`, `VAN`, `TRUCK`, `SUV`, `OTHER`.
   - Vehicle Statuses: `AVAILABLE`, `IN_USE`, `MAINTENANCE`, `OUT_OF_SERVICE`, `RETIRED`.
   - Soft-deletion via `archived_at` preserving all operational history.

2. **Vehicle Assignment (`vehicle_assignments`)**:
   - Tracks long-term or persistent vehicle driver assignments (`vehicle_id`, `driver_id`, `start_date`, `end_date`, `assignment_type`, `created_by_id`).

3. **Vehicle Trip (`vehicle_trips`)**:
   - Trip lifecycle (`id`, `vehicle_id`, `driver_id`, `case_id` [optional], `client_id` [optional], `purpose`, `destination`, `start_odometer`, `end_odometer`, `calculated_distance_km`, `start_time`, `end_time`, `status`, `checkout_condition`, `checkin_condition`, `notes`).
   - Lifecycle Statuses: `PLANNED`, `CHECKED_OUT`, `CHECKED_IN`, `CANCELLED`.
   - **PostgreSQL Lock**: Concurrent checkout attempts for the same vehicle are prevented via a PostgreSQL partial unique index on `(vehicle_id) WHERE status = 'CHECKED_OUT'`.

4. **Vehicle Maintenance (`vehicle_maintenance`)**:
   - Preventive and corrective service records (`id`, `vehicle_id`, `maintenance_type`, `scheduled_date`, `scheduled_odometer`, `completed_date`, `completed_odometer`, `provider_name`, `cost`, `description`, `status`, `notes`).
   - Types: `OIL_CHANGE`, `TIRE_SERVICE`, `BRAKES`, `INSPECTION`, `REPAIR`, `RECALL`, `OTHER`.
   - Statuses: `SCHEDULED`, `DUE`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.

5. **Vehicle Insurance Policy (`vehicle_insurance_policies`)**:
   - Policy records (`id`, `vehicle_id`, `provider_name`, `policy_number`, `effective_date`, `expiry_date`, `status`, `coverage_details`, `notes`). Preserves full renewal history.

6. **Vehicle Location (`vehicle_locations`)**:
   - Geographic coordinates (`id`, `vehicle_id`, `latitude`, `longitude`, `recorded_at`, `source`, `accuracy_meters`, `speed_kmh`, `heading_degrees`, `provider_event_id`).
   - Sources: `MANUAL`, `MOBILE`, `TELEMATICS`.

7. **Telematics Provider Link (`vehicle_telematics_links`)**:
   - Maps vehicles to external telematics providers (`id`, `vehicle_id`, `provider_name`, `external_vehicle_id`, `is_active`, `last_sync_at`).

8. **Fleet Geofence (`fleet_geofences`) & Events (`fleet_geofence_events`)**:
   - Service area boundary definitions (`id`, `name`, `geofence_type`, `center_latitude`, `center_longitude`, `radius_meters`, `polygon_geojson`, `is_active`) and boundary transition event logs (`ENTER`, `EXIT`).

## Consequences
- Vehicle check-out and check-in enforce atomic odometer monotonicity (ending odometer >= starting odometer).
- Case/Client linkages remain privacy-isolated from fleet operational users.
- Full historical preservation for trips, maintenance, and insurance renewals.
