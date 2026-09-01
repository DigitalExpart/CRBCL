# CRBCL Fleet Management Domain Specification

## Architecture Overview
The Fleet Management domain governs CRBCL's vehicle operations, vehicle check-out/check-in lifecycles, maintenance scheduling, insurance tracking, telematics integration, and geofencing foundation.

```
                  ┌────────────────────────┐
                  │     FleetService       │
                  └───────────┬────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
   ┌─────────────────┐ ┌──────────────┐ ┌───────────────┐
   │ Vehicle Registry│ │ Trip Lifecycle│ │  Telematics   │
   │ & Odometer Mon. │ │ & Checkout   │ │ Provider (Abs)│
   └─────────────────┘ └──────────────┘ └───────┬───────┘
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                           ┌─────────────────┐     ┌─────────────────┐
                           │ ManualProvider  │     │  FakeProvider   │
                           └─────────────────┘     └─────────────────┘
```

## Domain Subsystems

### 1. Vehicle Lifecycle & State Machine
- Statuses: `AVAILABLE` -> `IN_USE` -> `MAINTENANCE` -> `OUT_OF_SERVICE` -> `RETIRED`.
- Check-out only allowed from `AVAILABLE` state.
- Check-in updates odometer and returns vehicle to `AVAILABLE` unless flagged for maintenance.

### 2. Concurrent Checkout Prevention
- PostgreSQL partial unique index on `vehicle_trips (vehicle_id) WHERE status = 'CHECKED_OUT'` prevents race conditions.

### 3. Maintenance & Insurance Reminders
- Integrated with Phase 9 Notification & Reminder Engine.
- Sends alerts for upcoming maintenance (date/odometer) and expiring insurance policies (60/30/7 days).

### 4. Telematics & Geofencing Foundation
- Decoupled via `TelematicsProvider` abstract class.
- Supports circular (`center_latitude`, `center_longitude`, `radius_meters`) and polygon geofences with `ENTER` / `EXIT` event processing.
