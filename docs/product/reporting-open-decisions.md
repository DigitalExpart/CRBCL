# CRBCL Reporting & Quality Assurance — Open Decisions & Configuration Matrix

This document tracks policy decisions, default thresholds, and configurable items requiring formal sign-off from Chief Red Bear Children's Lodge leadership.

---

| # | Topic / Decision Area | Current Implementation Default | Pending CRBCL Confirmation / Options |
|---|---|---|---|
| **1** | **Recent Case Note Threshold** | 30 Days (Cases without a completed case note in 30+ days trigger a QA alert). | Confirm whether threshold should be 14 days, 30 days, or role-dependent (e.g. 14 days for high-risk protection cases). |
| **2** | **Long-Term Open Case Threshold** | 12 Months (Cases open for 365+ days flagged for permanency review). | Confirm whether 12 months matches CRBCL QA guidelines or if 6 months is preferred for voluntary cases. |
| **3** | **QA Audit Cadence Default** | Quarterly (90 Days) for protection cases; Semi-Annual (180 Days) for kinship/prevention. | Define exact audit cadence matrix per case type. |
| **4** | **Audit Tickler Grace Period** | 14 Days (Flagged as `DUE_SOON` 14 days prior to due date). | Confirm warning lead time for supervisors. |
| **5** | **Child Passport Content Sharing** | Permission-aware (Medical sections excluded unless user has `client.medical.read`). | Confirm whether external emergency foster home transfers require a redacted offline emergency card. |
| **6** | **Report Export Row Limits** | 5,000 rows for synchronous UI export; larger reports queued asynchronously. | Confirm maximum export volume policy. |
| **7** | **Report Sharing Visibility** | Private to owner, or shared with team (`PRIVATE`, `TEAM`, `AUTHORIZED_SHARED`). | Confirm whether cross-team report sharing requires Manager approval. |
