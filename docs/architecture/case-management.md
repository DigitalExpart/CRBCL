# CRBCL Architecture Decision Record & Case Management Specification

## Overview
The Core Case Management, Investigations & Case Notes module (Phase 4) delivers 360° family wellness case coordination, multi-child tracking, staff assignments, collateral sources, and immutable clinical documentation for the Chief Red Bear Children's Lodge platform.

---

## 1. Architecture Decision Records (ADRs)

### ADR-009: Strict Case Lifecycle State Machine
- **Context**: Cases must transition through formal, governed stages and statuses with audit logging. Direct arbitrary patching of case status is prohibited.
- **Decision**: Status transitions (such as closing or reopening) must execute through dedicated domain commands (`/close`, `/reopen`) requiring mandatory clinical justifications and recording entries in `case_status_history`.
- **Consequences**: Ensures legal accountability and audit readiness for Indigenous child welfare governance.

### ADR-010: Centralized Conflict-of-Interest Case Restrictions
- **Context**: Staff members who have personal or kin relationships with families involved in a case must be strictly prohibited from accessing case data.
- **Decision**: Conflict-of-interest restrictions are centrally enforced at the permission service layer (`PermissionService.check_case_access`). If an active restriction exists in `case_restrictions` for a user on a given case, all read, write, note, and roster requests are rejected with `HTTP 403 Forbidden` regardless of other role permissions.
- **Consequences**: Zero data leakage for restricted workers across API, list, and detail views.

### ADR-011: Immutable Clinical Case Notes & Legal Addenda
- **Context**: Child welfare case notes are legal records. Once completed and locked, historical notes cannot be modified or deleted.
- **Decision**: Locked case notes (`is_locked = true`) reject all update or delete requests. Clarifications, corrections, and new facts must be appended as child records (`case_note_addenda`) with author and timestamp tracking.
- **Consequences**: Permanent evidentiary integrity and compliance with child welfare evidentiary standards.

---

## 2. Relational Schema Summary
- `cases`: Root case table with atomic sequencing (`CRB-YYYYMM-NNNN`), stage, status, risk, and timestamps.
- `case_sequences`: Year-month counters with `SELECT ... FOR UPDATE` row locks.
- `case_people`: Case roster linking canonical `Person` records to cases with roles (`subject_child`, `parent`, `caregiver`, `extended_kin`, `band_rep`) and primary flags.
- `case_assignments`: Staff worker assignments (investigator, secondary, caseworker).
- `case_external_workers`: External contacts (Band Representatives, Legal Counsel, External Providers).
- `case_sources`: Collateral & Other information sources.
- `case_links`: Cross-case bidirectional links with prevention of self-linking.
- `case_restrictions`: Conflict-of-interest access blocks.
- `case_transfers`: Multi-team transfer requests with supervisor approval workflow.
- `case_status_history`: Audit trail for case lifecycle transitions.
- `case_notes`: Clinical case documentation with contact types, location, duration, well-child indicators, and lock flags.
- `case_note_addenda`: Append-only legal corrections for locked notes.
