# CRBCL Financial & Billing Architecture (Phase 10)

## 1. Domain Overview
Phase 10 provides the operational accounting backbone for Chief Red Bear Children's Lodge, encompassing:
1. **Financial Service Requests**: Purchase Orders (`PO-...`) and Staff Reimbursements (`RR-...`).
2. **Budget Lines & Funding Sources**: Program allocations, fiscal years, and expenditure rollups.
3. **Placement Billing Engine**: Per-diem invoice generation based on actual `PlacementEpisode` stays and versioned rate schedules.
4. **Billing Ledger & Immutability**: Historical snapshots, duplicate billing prevention, and auditable voiding.
5. **Security & Financial Controls**: Granular permissions, segregation of duties (self-approval blocked), and case-restriction privacy masking.

---

## 2. Core Entity Architecture

```
[Funding Sources] ────< [Budget Lines] ────< [Service Request Items] >──── [Service Requests]
                                                                                  │
                                                                         [Approvals Workflow]
                                                                                  │
                                                                           [Outbox Events]

[Placement Episodes] ───┐
                        ├──> [Placement Billing Service] ───> [Invoices] ───< [Invoice Items]
[Billing Rates (v1/v2)] ┘                                                                │
                                                                               [Immutable Snapshots]
```

---

## 3. Key Capabilities & Rules
- **Decimal Calculation Authority**: All arithmetic computed server-side using `decimal.Decimal` with `ROUND_HALF_UP` precision.
- **Segregation of Duties**: Requestor cannot approve their own financial requests (`403 Forbidden`).
- **Placement Day Intersections**: Billable days calculated deterministically using inclusive stay boundaries (`(end - start).days + 1`).
- **Rate Versioning**: Rates are time-stamped with `effective_from` and `effective_to`, ensuring historical calculations remain exact.
- **Privacy Masking**: Users with finance permissions can view case-linked financial allocations without leaking confidential clinical case notes or restricted files.
