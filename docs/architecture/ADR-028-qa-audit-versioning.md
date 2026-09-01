# ADR-028: QA Checklist Template Versioning & Audit Tickler Engine

## Status
Accepted

## Context
Quality Assurance in child welfare requires structured case audits against standardized compliance checklists. However, QA compliance standards evolve over time. Modifying an existing audit template checklist must not retroactively change the meaning or scoring of historical completed audits. Furthermore, supervisors need an automated audit tickler to track recurring case review cadences (monthly, quarterly, semi-annually) without relying on manual reminders.

## Decision
We implement a **Versioned QA Checklist System and Automated Audit Tickler Engine**.

### 1. Template Versioning Architecture:
- `qa_audit_templates` stores the overarching template metadata (e.g., "Standard Child Protection Case Audit").
- `qa_audit_template_versions` maintains immutable versions of the checklist. When a template is edited, a new version is created.
- `qa_audit_template_items` are bound to a specific `version_id`.
- `qa_audits` reference a specific `template_version_id`. Once created, an audit's checklist questions are frozen.

### 2. Audit Item Responses & Findings:
- Audit items support `YES`, `NO`, or `N/A` responses, plus notes, finding severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and follow-up requirements.
- Completed audits enter state `COMPLETED` and become immutable. Corrections require formal addendums or administrative override logging.

### 3. Audit Tickler Engine:
- Calculates audit due status based on template cadence:
  - `MONTHLY`: 30 days since last completed audit
  - `QUARTERLY`: 90 days since last completed audit
  - `SEMI_ANNUAL`: 180 days since last completed audit
  - `ANNUAL`: 365 days since last completed audit
- Dynamic status classification:
  - `OK`: Last audit completed within threshold minus 14 days.
  - `DUE_SOON`: Due within next 14 days.
  - `OVERDUE`: Past due date or case never audited.
- Completing a new audit immediately advances the case's tickler status to `OK`.

## Consequences
- Historical audits remain 100% faithful to the exact checklist version active when conducted.
- QA supervisors have real-time visibility into compliance health and overdue case reviews.
