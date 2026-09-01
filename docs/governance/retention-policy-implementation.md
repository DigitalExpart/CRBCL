# CRBCL Record Retention & Legal Hold Implementation Architecture

## 1. Lifecycle States

Records within the CRBCL platform transition through six technical lifecycle states:

1. **ACTIVE**: Live operational record. Modifiable by authorized users according to practice rules.
2. **LOCKED / IMMUTABLE**: Completed record (Case Note, Assessment, Safety Plan, Invoice) locked against modification.
3. **ARCHIVED**: Closed case or historic file maintained for statutory retention. Read-only.
4. **RETENTION HOLD / LEGAL HOLD**: Active override preventing disposal or archiving due to litigation, audit, or inquiry.
5. **ELIGIBLE FOR DISPOSAL**: Retention period expired with no active legal holds.
6. **DISPOSED**: Formally purged via governed, audited deletion routine.

---

## 2. Legal Hold Architecture

- **Database Attributes**:
  - `cases.is_legal_hold` (Boolean, indexed)
  - `cases.legal_hold_reason` (Text)
  - `cases.legal_hold_by_id` (UUID foreign key to `users`)
  - `cases.legal_hold_at` (Timestamp)
- **Enforcement Mechanics**:
  - Any attempt to soft-delete, hard-delete, archive, or dispose of a record linked to a Case where `is_legal_hold == True` raises a `LegalHoldError`.
  - Legal hold overrides statutory retention expiration.
  - Applying or lifting a legal hold generates an immutable `AuditEvent` with `action="LEGAL_HOLD_APPLIED"` or `"LEGAL_HOLD_REMOVED"`.

---

## 3. Record Correction vs Deletion

To maintain legal integrity in child welfare proceedings:
- **Case Notes**: Cannot be deleted or edited after sign-off. Corrections must be submitted as an attached `CaseNoteAddendum`.
- **Assessments & Plans**: Locked upon completion. Re-opening creates a new version with a audit log of the Director unlock event (`AssessmentUnlockEvent`).
- **Financial Invoices**: Issued invoices cannot be altered; credit notes or adjustments must be recorded as distinct ledger entries.
