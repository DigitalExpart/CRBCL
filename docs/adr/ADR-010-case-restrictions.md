# ADR-010: Centralized Case Restrictions and Conflict-of-Interest Controls

## Status
Accepted

## Context
In small or closely knit First Nations communities, agency caseworkers, supervisors, or administrators may be related to children, caregivers, or families subject to a referral or active case. A conflict of interest arises whenever an employee's personal connections, kinship ties, or supervisory conflicts could bias casework decisions or compromise child and family privacy.

## Decision
1. Implement a first-class `case_restrictions` relational table linking `case_id` and `user_id` with restriction types (e.g. `conflict_of_interest`, `family_member_involved`, `supervisor_restricted`, `other`), reason, creation metadata, and expiration/removal audit records.
2. Enforce case restrictions **centrally at the backend authorization layer** (`PermissionService` and route dependencies).
3. The evaluation flow is strictly tiered:
   ```
   Authenticated User
          ↓
   Role Capabilities (e.g. case.read)
          ↓
   Team Scope Validation
          ↓
   CASE RESTRICTION CHECK (is_user_restricted_from_case)
          ↓
   Field-Level Policy
          ↓
   ALLOW / DENY (403 Forbidden)
   ```
4. A restricted user who directly invokes any API endpoint for that case (e.g. `GET /api/v1/cases/{id}`, case notes, timeline, snapshot) is immediately denied with `HTTP 403 Forbidden`, even if they possess global `case.read` or admin permissions.
5. In case lists and linked case references, restricted cases have their sensitive narrative, title, and client names masked to prevent metadata leakage.
6. Case restrictions are never physically deleted from the database; lifting a restriction sets `is_active = FALSE`, `removed_at`, `removed_by`, and records `removal_reason`.

## Consequences
- Guarantees strict compliance with Miyo Pimatisowin Act confidentiality rules and child welfare conflict-of-interest mandates.
- Eliminates client-side security bypasses.
- Provides a verifiable log of when conflicts were declared, who approved them, and when they were resolved.
