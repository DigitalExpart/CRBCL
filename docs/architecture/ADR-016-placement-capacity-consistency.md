# ADR-016: Child Placement Concurrency & Primary Placement Invariants

## Status
**ACCEPTED** (Phase 7 — Active Efforts, Removals, Placements & Court Operations)

## Context
In child protection and family wellness casework, a child cannot legally or physically reside in more than one active primary placement at any given point in time. Conflicting or concurrent active placement records can cause severe operational errors, such as duplicate per diem billing, conflicting court submissions, and misallocated caseworker supervision.

Furthermore, temporary respite stays (e.g. weekend cultural respite or relief foster care) occur while a primary placement remains intact, whereas a discharge or transfer permanently concludes the primary placement.

## Decision
We enforce the following core architectural invariants:

1. **Single Active Primary Placement Invariant**:
   - For any child (`child_id` / `person_id`), there can be at most **one** `placement_episode` with status in `('ACTIVE', 'DISRUPTED')` and at most **one** `in_home_placement` with status `ACTIVE`.
   - Starting a new primary placement episode requires either:
     - The previous placement episode has a completed `discharge_episode` (status `COMPLETED` / `DISCHARGED`), or
     - The previous placement is marked `TRANSFERRED` with an explicit discharge/transfer timestamp.
   - Attempting to activate a concurrent placement for a child with an existing active primary placement raises a `409 Conflict` domain error (`ConcurrentActivePlacementError`).

2. **Transactional Concurrency Control**:
   - Placement activations, transfers, respite bookings, and discharges execute with row-level pessimistic locking (`SELECT ... FOR UPDATE` on child/case or placement records) to prevent race conditions during concurrent worker submissions.

3. **Respite vs Primary Placement Invariant**:
   - A `respite_episode` is always subordinate to a parent `placement_episode_id`.
   - A respite episode does NOT mutate the primary placement's `ACTIVE` status.
   - Multiple respite intervals can be scheduled across the timeline of a placement, but cannot have overlapping active date ranges for the same placement.

4. **Separation of Concerns: Phase 7 (Episodes) vs Phase 8 (Licensing)**:
   - In Phase 7, placement records capture provider names, contact references, provider types, and financial rates.
   - Phase 8 will introduce the comprehensive **Placement Homes & Licensing Engine** (bed capacity management, safety inspections, provider licensing lifecycles, and home roster management) without requiring schema rewrites to Phase 7 placement episodes.

## Consequences

### Positive
- Guarantees referential and operational consistency across all child placements.
- Prevents double-counting, ghost placements, and ambiguous legal custody states.
- Clean foundation for Phase 8 provider licensing and capacity tracking.

### Negative / Complexity
- Service operations must perform atomic validation checks and pessimistic lock acquisition within database transactions.
