# ADR-013: Plan Versioning, Cloning, and Immutability

**Status:** Approved  
**Date:** 2026-08-31  
**Deciders:** CRBCL Architecture & Clinical Practice Review Board  
**Technical Context:** CRBCL Family Wellness Case Management Platform — Phase 6  

---

## Context & Problem Statement

Family Safety Plans and Case Plans are critical legal, clinical, and community documents within the Cowessess First Nation child welfare practice.

During the lifespan of a case, family needs evolve:
1. Immediate safety threats require urgent **Safety Plans** that specify danger statements, caregiver protective actions, and kinship supervision.
2. Long-term family wellness requires comprehensive **Case Plans** setting measurable goals, target dates, and multi-party activities.
3. Family wellness meetings occur periodically (e.g. quarterly or upon significant milestones), requiring updates to running plans or establishing new planning sessions.

Historically, legacy case management software suffered from two failure modes:
- **Destructive in-place edits:** Workers overwritten historical goals, progress notes, and signed agreements without audit trails.
- **Uncontrolled copy-paste:** Creating new plans copied stale signatures, obsolete lock states, or outdated completion timestamps.

CRBCL requires an immutable, version-controlled Plan architecture that preserves historical integrity while offering seamless planning workflows.

---

## Decision Drivers

1. **Indigenous Sovereignty & Accountability:** Complete transparency and tamper-evident history of all commitments made between the Lodge, families, and Elders.
2. **Clinical Continuity:** Workers must easily view the progression of family goals across time without losing past commitments.
3. **Controlled Immutability:** Once finalized and signed, a plan version cannot be silently altered.
4. **Clean Session Cloning:** Workers must be able to base a new planning session on prior goals without carrying over stale signatures, completion stamps, or lock states.
5. **Unified Domain Core:** Avoid maintaining two distinct database subsystems for Safety Plans vs Case Plans; use a unified `Plan` + `PlanVersion` domain with type discriminators.

---

## Architectural Decision

### 1. The Plan — Plan Version Hierarchy

We establish a two-tier relational hierarchy:
```
Plan (Master File: case_id, plan_type, plan_number, status, current_version_id)
  └── PlanVersion (Version Snapshot: version_number, status, meeting_date, narrative, document_hash)
        ├── PlanParticipants (Relational meeting roster & signature requirements)
        ├── PlanConcerns (Harm statements, danger statements, worries)
        ├── PlanStrengths (Caregiver capacities, kinship & cultural strengths)
        ├── PlanGoals (Categorized family goals & target dates)
        │     ├── PlanActivities (Tasks with responsible assignees & due dates)
        │     └── GoalProgressUpdates (Longitudinal progress entries)
        ├── PlanAssessments (Links to originating/informing assessments)
        └── PlanSignatures (Cryptographically bound signature attestations)
```

### 2. Version Lifecycle State Machine

Each `PlanVersion` transitions through strict sequential states:
```
DRAFT ──► IN_REVIEW ──► FINALIZED ──► LOCKED
  │           │            │
  └───────────┴────────────┴──────► CANCELLED
```

- **`DRAFT`:** Editable by assigned caseworkers with `plan.update`. Goals, activities, concerns, and strengths can be added, updated, or reordered.
- **`IN_REVIEW`:** Submitted to supervisor for clinical review (via `WorkflowService`).
- **`FINALIZED`:** Approved by supervisor / finalized by caseworker. A canonical SHA-256 `document_hash` is computed. Ready for electronic signatures.
- **`LOCKED`:** Fully executed and sealed. Direct modifications are strictly forbidden. Unlocking requires Director privilege with mandatory justification.
- **`CANCELLED`:** Voided or superseded prior to execution.

### 3. Plan Progression Modes: Running Plans vs. Cloned Sessions

We support two distinct operational patterns:
- **Mode A: Controlled Version Creation (`POST /plans/{id}/versions`):** Increments version number on an existing running plan (e.g. Version 1 -> Version 2) when continuing work with the same family on an active plan.
- **Mode B: Cloned Planning Session (`POST /plans/{id}/clone`):** Creates a brand new `Plan` instance with its own unique `PLN-YYYYMM-NNNN` number, cloning structural elements (concerns, strengths, active goals, open activities) from a prior plan.

### 4. Strict Cloning Rules

When cloning a plan version:
- **COPIED:** Plan type, title, concerns/harm statements, strengths/protective factors, active goals, and uncompleted activities.
- **EXCLUDED (STRIPPED):**
  - Signatures (`plan_signatures` are never copied).
  - Finalized/locked timestamps (`finalized_at`, `locked_at`, `locked_by`).
  - Document hashes (`document_hash` reset to null).
  - Activity completion timestamps (`completed_at`, `completion_notes` reset for open tasks).
  - Completed goals can be optionally carried over as reference or filtered out.

---

## Consequences & Compliance

- **Integrity:** Past versions are permanently preserved and queryable by version number.
- **Legal Defensibility:** Every signed document reflects the exact state of the plan at the moment of signature.
- **Performance:** Relational child tables allow targeted SQL queries and direct aggregation without JSON parsing.
