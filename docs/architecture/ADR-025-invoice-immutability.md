# ADR-025: Invoice Immutability, Calculation Snapshots, and Controlled Void Lifecycle

## Status
Accepted (Phase 10)

## Context
Invoices issued to placement homes and funders represent legal accounting artifacts. If a client's date of birth or a historical rate table is later amended, existing finalized invoices must not retroactively change.

## Decision
1. **Calculation Snapshot Pattern**:
   - When an invoice is created, all calculation variables (`child_name`, `age_at_service`, `rate_band_label`, `billable_days`, `daily_rate`, `line_total`, `is_federally_eligible`) are permanently snapshotted in `invoice_items`.
   - Rendered invoices and ledger reports read directly from snapshot columns rather than performing dynamic joins against current rate tables.
2. **Draft vs Finalized Lifecycle**:
   - `DRAFT` / `GENERATED` invoices may be recalculated or regenerated if placement details are updated prior to sign-off.
   - `FINALIZED` invoices are locked and strictly immutable. Any modification to `PlacementEpisode`, `Person`, or `BillingRate` has zero impact on finalized invoice records.
3. **Duplicate Billing Protection**:
   - A placement home cannot have two finalized invoices covering overlapping billing periods.
   - Enforced by unique constraints / deterministic idempotency keys.
4. **Controlled Void Lifecycle**:
   - Finalized invoices cannot be deleted (`DELETE` prohibited).
   - Voiding requires the `finance.invoice.void` capability, a mandatory recorded `void_reason`, and records the actor and timestamp (`voided_by`, `voided_at`).
   - Voided invoices remain visible in the ledger for complete accounting reconciliation.

## Consequences
- **Positive**: Complete financial audit integrity, zero retroactive accounting discrepancies, and immutable billing ledgers.
- **Negative**: Corrections after finalization require explicit voiding and regeneration.
