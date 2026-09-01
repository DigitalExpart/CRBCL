# CRBCL Legacy Data Inventory & Migration Mapping

## 1. Legacy Data Source Inventory

| Legacy Source | Format / System | Estimated Records | Data Categories | Data Quality Risk | Ownership |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Base44 Historic Archive** | CSV / JSON Exports | ~1,200 Records | Clients, Cases, Intake Referrals | Duplicate names, missing DOBs | CRBCL IT |
| **RedMane Legacy System** | SQL Dump | ~3,500 Records | Historical Child Welfare Cases | Legacy code mapping inconsistencies | CRBCL |
| **Paper Form Scanning** | PDF Documents | ~450 Files | Assessment & Placement History | OCR extractions require human review | CRBCL |

---

## 2. Source-to-Target Mapping Rules

- **Clients & Persons**:
  - Source `client_id` mapped to `MigrationLedger` (`source_system="BASE44"`, `target_entity_type="CLIENT"`).
  - Deduplication matching executed against `first_name`, `last_name`, and `date_of_birth`.
  - Canonical `Person` record generated automatically upon `Client` creation.
- **Cases & Incidents**:
  - Source case numbers preserved in `cases.case_number` with legacy prefix (`LEG-`).
- **Notes & History**:
  - Legacy notes imported as locked, read-only `CaseNote` records marked with `is_legacy=True`.

---

## 3. ETL Pipeline & Reconciliation Protocol

```
Extract Legacy Records -> Profile & Clean -> Transform Schemas -> Validate Integrity -> Load into CRBCL -> Reconcile Ledger
```

- **Reconciliation Requirement**: Every migration batch must achieve 100% reconciliation matching between source record count and `MigrationLedger` entries (`status="COMPLETED"` or `"MERGED"`).
