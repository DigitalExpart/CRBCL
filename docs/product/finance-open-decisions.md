# CRBCL Finance & Billing — Open Decisions & Configuration Matrix

This document tracks unresolved policy choices, assumptions, and configurable items requiring formal sign-off from Chief Red Bear Children's Lodge leadership.

---

| # | Topic / Decision Area | Current Implementation Default | Pending CRBCL Confirmation / Options |
|---|---|---|---|
| **1** | **Fiscal Year Boundary** | April 1 – March 31 (standard Canadian Indigenous Services fiscal year). | Confirm whether CRBCL operates on April 1 – March 31 or calendar year (Jan 1 – Dec 31). |
| **2** | **Tax Treatment (GST/PST)** | Configurable tax percentage (default `0.00%` for tax-exempt Band operations, support for standard 5% GST where applicable). | Confirm tax-exemption status for on-reserve purchases vs off-reserve commercial vendor invoices. |
| **3** | **Approval Dollar Thresholds** | Configurable approval steps (Caseworker -> Supervisor -> Manager/Director). | Define exact dollar threshold matrix (e.g. Under \$1,000 = Supervisor; \$1,000–\$5,000 = Manager; Over \$5,000 = Executive Director). |
| **4** | **Placement Day Calculation Boundaries** | Inclusive day count (`(end_date - start_date).days + 1`). | Confirm if discharge day is billed as a full day, half day, or excluded if discharged prior to 12:00 PM. |
| **5** | **Respite Stay Billing Treatment** | Respite days billed to respite provider without double-billing primary home capacity. | Confirm whether primary home receives a retainer/holding allowance during approved temporary respite. |
| **6** | **Payment Reconciliation & Bank Integrations** | Invoice status transitions through `FINALIZED` -> `PAID` via administrative confirmation. | Direct EFT / direct deposit file generation (CPA005 / NACHA) deferred to future ERP integration phase. |
