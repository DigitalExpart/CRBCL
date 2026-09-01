# ADR-034: Microsoft Graph Integration & Outlook Calendar Source-of-Truth Model

## Context
CRBCL staff rely on Microsoft Outlook for daily personal scheduling, while CRBCL Platform Calendar serves as the authoritative legal system-of-record for child welfare appointments, home visits, and court hearings.

## Decision
1. **CRBCL Calendar as Single Source-of-Truth**: The CRBCL database remains the sole authoritative calendar. Events are pushed outbound from CRBCL to Outlook (`CRBCL Calendar -> Outbox Sync -> Outlook`). External changes in Outlook do not silently overwrite CRBCL case schedules.
2. **Data Minimization**: External Outlook event titles and descriptions contain zero client names, case numbers, allegation details, or foster home addresses. Events are formatted using privacy-safe templates (e.g., `CRBCL Appointment`, `Case Staffing Session`).
3. **Idempotency & Mapping**: External sync uses an explicit `integration_external_links` table mapping `(internal_event_id, provider='MICROSOFT', external_event_id)`. Re-running a sync job updates existing external events rather than creating duplicates.
4. **Failure Isolation**: Sync runs in background outbox tasks. If Microsoft Graph returns HTTP 500 or 401, the CRBCL appointment remains saved and valid, and the sync error is logged for retry.

## Status
Accepted.
