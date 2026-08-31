# ADR-018: Placement Home & Facility Domain Model

## Status
Accepted

## Date
2026-08-31

## Context
In Phase 7, the CRBCL platform introduced the legal removal and child placement episode lifecycle (`placement_episodes`). While Phase 7 captured destination details as string/contact attributes (`provider_name`, `provider_address`, `provider_contact`), CRBCL requires a formal, auditable operational directory of care destinations:
- Licensed Foster Homes
- Therapeutic Care Homes
- Customary Care & Kinship Homes
- Relative Care Homes
- Group Care Facilities and Specialized Treatment Centers

These destinations require independent lifecycles, licensing terms, household members, caregiver background checks, routine inspections/visits, contact logs, home safety assessments, and real-time bed capacity tracking.

---

## Decisions

### 1. Entity Distinction: Placement Home vs. Provider vs. Household
- **`Provider` (`providers`)**: Represents clinical or professional organizations/individuals (physicians, therapists, clinics, external agencies). A `PlacementHome` may optionally reference a `provider_id` when operated by an organization.
- **`Household` (`households`)**: Represents a natural family dwelling unit associated with clients/cases.
- **`PlacementHome` (`placement_homes`)**: Represents an authorized, inspected, and potentially licensed care destination managed by or partnered with the Child & Family Wellness Agency.

### 2. Capacity Model & Concurrency Protection
- **Capacity Definition**:
  - `total_capacity` / `total_beds`: Approved bed limit ($N \ge 0$).
  - `occupied_beds`: Derived dynamically as:
    $$\text{occupied\_beds} = \text{Count}(\texttt{placement\_episodes}) \text{ where } \texttt{placement\_home\_id} = \text{Home.id} \land \texttt{status} = \text{'ACTIVE'}$$
  - `available_beds`: $\max(0, \text{total\_capacity} - \text{occupied\_beds})$.
- **Concurrency Control**:
  - To prevent overbooking when two caseworkers place children simultaneously, placement activation operations acquire a PostgreSQL row lock:
    ```sql
    SELECT * FROM placement_homes WHERE id = :home_id FOR UPDATE;
    ```
  - If $\text{occupied\_beds} \ge \text{total\_capacity}$, the service raises `409 Conflict` ("Placement Home capacity reached").
  - On placement discharge (`status = 'COMPLETED'` or `'DISCHARGED'`), capacity is immediately and automatically restored.
  - Respite care episodes link to the primary placement and do not release or double-consume primary bed capacity.

### 3. Licensing Lifecycle & Historical Immutability
- `placement_home_licenses` maintains a full historical audit trail of all applications and licenses.
- Renewal operations transition the prior active license to `EXPIRED` or `SUPERSEDED` and insert a new `ACTIVE` license record with its effective and expiry dates.
- Expiration monitoring queries alert supervisors at 90, 60, and 30 days prior to expiry via the transactional outbox.

### 4. Assessment Engine Reuse
- Instead of building a redundant survey engine, Phase 8 extends Phase 5's versioned Assessment Engine by adding `assessments.placement_home_id`.
- The versioned `HOME_ASSESSMENT` template evaluates physical dwelling safety, environmental standards, and caregiver preparedness with full revisioning, locking, and supervisory approval workflows.

### 5. Background Check Integration
- Home members (`placement_home_members`) link directly to canonical `persons.id`.
- Background checks reuse the polymorphic `background_checks` model from Phase 7 (`subject_type = 'PLACEMENT_MEMBER'`, `subject_id = member.id` or `person_id`), providing unified CPIC, CAR, and Band Elder screening.

### 6. Privacy & Field-Level Security
- Exact home coordinates and physical addresses are protected by `placement_home.map.read` and `placement_home.read`.
- When viewing historical placements on a home record, if the user lacks access to a child's restricted case, child names and sensitive case identifiers are redacted while maintaining chronological placement duration.

---

## Consequences

### Positive
- Strict transactional consistency for bed occupancy without counter drift or overbooking.
- Clean separation of concerns between clinical providers, family households, and licensed placement destinations.
- Complete regulatory and legal audit trail for licensing and caregiver screening.
- Full reuse of Phase 5 Assessment Engine and Phase 7 Background Checks.

### Neutral / Trade-offs
- Placement creation requires an active database transaction with row-level locking for homes with finite capacity.
