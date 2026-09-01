# ADR-019: Unified Calendar Event Model & Scheduling Layer

## Status
Accepted (Phase 9)

## Context
The CRBCL Family Wellness platform handles temporal commitments and deadlines across multiple operational domains:
- Clinical and Caseworker Appointments
- Case Note Follow-up Appointments (`CaseNote.next_appointment_at`)
- Child Protection Court Hearings (`CourtEvent`)
- Family Visitation Schedules (`VisitationPlan`)
- Multi-disciplinary Staffing Sessions (`StaffingSession`)
- Assessment deadlines and reviews (`Assessment`)
- Family Safety and Case Plan meetings, goals, and activity deadlines (`PlanGoal`, `PlanActivity`)
- Placement Home licensing renewal and visit follow-ups (`PlacementHomeLicense`, `PlacementHomeVisit`)
- Background check expirations (`BackgroundCheck`)

Previously, these domains maintained independent date columns, causing fragmented visibility and requiring workers to navigate multiple screens to understand their daily or weekly schedule.

## Decision

### 1. Single Source of Truth & Materialized Scheduling Representation
- Specific domain entities remain the **authoritative source of truth** for their respective business records (e.g., `CourtEvent` is authoritative for legal hearings, `StaffingSession` is authoritative for staffing proceedings, `VisitationPlan` is authoritative for parental contact agreements).
- The `calendar_events` table provides a **unified scheduling representation** for querying, filtering, team aggregation, and reminder triggering.
- Standalone events (e.g., custom caseworker appointments, follow-ups, and staffing sessions) are directly authored in `calendar_events` or synchronized in the same transaction as domain updates.
- Updates to authoritative domain models automatically synchronize or emit outbox events to keep the calendar representation consistent.

### 2. Event Types & Stable Keys
Calendar events use strict machine keys:
- `APPOINTMENT`
- `COURT`
- `VISITATION`
- `CASE_NOTE_FOLLOWUP`
- `STAFFING`
- `ASSESSMENT`
- `PLAN_MEETING`
- `HOME_VISIT`
- `OTHER`

### 3. Timezone Strategy
- All timestamps in PostgreSQL are stored as UTC timezone-aware datetimes (`TIMESTAMPTZ` / `DateTime(timezone=True)`).
- Operational scheduling defaults to Saskatchewan local time (`America/Regina` / UTC-6 without Daylight Saving Time shifts).
- All date-range queries accept UTC bounds, while frontends render local time with explicit timezone labels.

### 4. Bounded Recurrence
- For recurring schedules (such as weekly or bi-weekly family visitation plans), recurrence rules are structured via `calendar_recurrence_rules` (`frequency`, `interval`, `by_weekday`, `until_date`, `max_occurrences`).
- Arbitrary unvalidated RRULE strings are prohibited.
- The calendar query engine generates recurrence occurrences **strictly bounded by the requested view window** (e.g., maximum 90 days query range) to prevent infinite materialization and unbounded memory consumption.

### 5. Case Restriction & Privacy Redaction
- When a user views `/schedule` or `/schedule/team`, any calendar event linked to a `case_id` where the viewing user has an active `CaseRestriction` is dynamically redacted:
  - `title` is masked to `"Unavailable / Busy"`
  - `description`, `location`, `case_id`, `person_id`, and `source_entity_id` are stripped from the response payload.
  - The slot displays as occupied to prevent scheduling collisions while completely preventing confidential child, case, or court details from leaking.

## Consequences
- **Positive**: Single endpoint for all personal and team schedule views (`/api/v1/calendar/my-schedule` and `/api/v1/calendar/team-schedule`).
- **Positive**: Zero data duplication of sensitive legal/clinical narratives into calendar tables.
- **Positive**: Guaranteed privacy preservation across case restriction boundaries.
