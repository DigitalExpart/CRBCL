# ADR-024: Placement Billing Engine, Rate Versioning, and Deterministic Date Intersections

## Status
Accepted (Phase 10)

## Context
Placement Homes (foster homes, customary kinship care, and group facilities) receive per-diem maintenance and care compensation based on actual placement episodes. Per-diem rates vary by facility type, child age bracket, and fiscal period.

## Decision
1. **Authoritative Source of Placement Dates**:
   - `PlacementEpisode` records in the primary database are the sole source of truth for placement stay dates.
   - Manual re-entry of placement dates or billable days is prohibited.
2. **Deterministic Placement Day Calculation**:
   - For a given billing period `[period_start, period_end]` and a placement episode `[placement_start, placement_end]`:
     - `effective_start = max(period_start, placement_start)`
     - `effective_end = min(period_end, placement_end or period_end)`
     - If `effective_end < effective_start`, `billable_days = 0`.
     - `billable_days = (effective_end - effective_start).days + 1` (inclusive standard).
     - Post-discharge days are automatically excluded since `placement_end` terminates the interval.
3. **Child Age Determination on Service Dates**:
   - Child age is derived from `Person.date_of_birth` relative to the actual service dates in the billing period.
   - If a child transitions across an age boundary during the billing period, billing splits into sub-intervals matching the applicable rate brackets.
4. **Historical Rate Versioning**:
   - Invoices lookup `billing_rates` where `effective_from <= service_date <= (effective_to or max_date)`.
   - Modifying a rate schedule for future periods never affects invoices calculated for historical periods.
   - Ambiguous overlapping active rate schedules for the same home type and age bracket are rejected by database validation.
5. **Explicit Federal Eligibility**:
   - Federal vs Band funding eligibility must be an explicitly recorded field (`is_federally_eligible`), never inferred solely from Indigenous identity.

## Consequences
- **Positive**: Exact, auditable placement compensation that strictly reflects actual care provided without manual arithmetic errors.
- **Negative**: Requires multi-interval rate matching when rate effective dates or child birthdays fall mid-month.
