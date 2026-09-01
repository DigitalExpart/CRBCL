# ADR-032: Fleet Location Privacy, Access Control & Data Retention Policy

## Status
Approved

## Context
Vehicle GPS tracking data contains sensitive operational information, worker movement history, and potential proxy data regarding client/case transportation routes. Unlimited or unmonitored location tracking risks employee privacy infringement and potential confidential client case leakage.

## Decision

### 1. Zero Background Surveillance Principle
- Mobile/browser location capture is strictly **action-triggered** (e.g. worker explicit check-out, manual location update button click).
- Continuous background browser tracking without explicit worker consent and clear active visual indicators is prohibited.

### 2. Fine-Grained Location Capabilities
Location data access is decoupled from general fleet view access:
- `fleet.vehicle.read`: Permits viewing vehicle directory, status, make/model, and mileage.
- `fleet.location.read`: Permits viewing current/last-known vehicle location on maps.
- `fleet.location.history`: Permits viewing historical location breadcrumbs and movement logs.
- `fleet.location.capture`: Permits submitting manual or browser GPS coordinates.

### 3. Privacy Masking & Stale Location Transparency
- Map views and API endpoints must clearly label stale locations (`is_stale: true` if last position update exceeds 60 minutes). Stale locations must never be represented as live active tracking.
- Client/case details attached to trips are **redacted** for fleet operational users lacking clinical case permissions (`case.read`). Only generic trip references (`Service Transportation`) are displayed.

### 4. Retention & Archival Strategy
- Active vehicle location ping history (`vehicle_locations`) is retained online for 90 days.
- Location records older than 90 days are archived or aggregated into summary trip mileage totals.

## Consequences
- Protects staff privacy and prevents unmonitored surveillance.
- Maintains strict compliance with CRBCL client confidentiality boundaries.
