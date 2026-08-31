# ADR-017: Background Check Subject Polymorphism & Placement Safety Adjudication

## Status
**ACCEPTED** (Phase 7 — Background Checks & Placement Safety Screening)

## Context
Child welfare safety protocols require extensive background screening before any individual may serve as an in-home caregiver, kinship provider, customary caregiver, foster parent, volunteer, or adult household member.

Screening subjects originate from diverse entities across the platform:
- Registered platform Clients (`clients`)
- Family members, relatives, or associated persons (`persons`)
- External placement providers and respite caregivers
- Community volunteers and agency staff

Rather than creating rigid, fragmented check tables for each person type, a unified, auditable screening engine is required.

## Decision
We implement a unified, polymorphic background screening entity (`background_checks`):

1. **Polymorphic Subject Identifiers**:
   - `subject_type`: `CLIENT`, `PERSON`, `PLACEMENT_PROVIDER`, `VOLUNTEER`, `STAFF`, `OTHER`.
   - `subject_id`: UUID of the referenced entity (nullable if external non-system person).
   - `subject_name`: Full legal name of the screening subject for human verification and cross-referencing.

2. **Screening Check Types**:
   - `CRIMINAL_RECORD`: RCMP / municipal police information check.
   - `CHILD_ABUSE_REGISTRY`: Provincial child protection registry check.
   - `VULNERABLE_SECTOR`: Enhanced vulnerable sector fingerprint and police screening.
   - `REFERENCE_CHECK`: Kinship and professional character references.

3. **Adjudication Lifecycle & Expiry Governance**:
   - Status transitions: `PENDING` -> `PASSED` | `FAILED` | `CONDITIONAL` | `EXPIRED`.
   - `is_eligible_for_placement`: Boolean flag indicating clearance for child custody or caregiving.
   - `adjudicated_by` (UUID FK -> `users.id`) and `adjudicated_at` (TIMESTAMPTZ): Mandatory audit trail for clinical or supervisor sign-off.
   - `expiry_date`: Supports automatic or scheduled expiration of annual screening clearances.

4. **Integration with Placements & In-Home Safety**:
   - Kinship and Customary Care placement workflows query the background check engine to verify that prospective caregivers hold active, non-expired `PASSED` clearances prior to placement approval.

## Consequences

### Positive
- Unified screening registry for all individuals involved in child care and agency operations.
- Direct auditability of who cleared an individual, when, and under what reference numbers.
- Prevents placement of vulnerable children with unverified or failed caregiver applicants.
