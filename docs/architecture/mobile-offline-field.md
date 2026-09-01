# CRBCL Mobile Offline Field Operations Guide

## 1. Field Caseworker Capabilities Matrix

| Workflow | Online Capability | Offline Field Capability | Sync Mechanism |
| :--- | :--- | :--- | :--- |
| **Case Review** | View complete case history, documents, family genogram | View assigned case summaries & contacts cached locally | Automated Pull Delta |
| **Case Note Drafting** | Create, sign, attach files, dispatch notifications | Draft case notes & addendums stored in local SQLite queue | Outbox Push Batch |
| **Safety Plan Review** | View and edit active safety plan activities | View active safety plan steps and record completion status | Outbox Push Batch |
| **Photo / File Capture** | Upload directly to cloud storage signed URL | Capture photos locally; stored encrypted on device storage | Background Chunked Sync |
| **Client Search** | Full database text search | Search within locally cached assigned clients | Local SQLite Index |

---

## 2. Sync Status Indicators

The mobile app displays clear sync status headers:
- **GREEN (Synced)**: All local mutations uploaded; connected to CRBCL cloud backend.
- **YELLOW (Pending Sync [N items])**: Active local mutations queued in SQLite outbox awaiting network reconnection.
- **RED (Offline)**: Device disconnected; operating in full local encrypted mode.

---

## 3. Remote Wipe & Lost Device Protocol

1. If a caseworker loses a mobile device:
   - Notify CRBCL IT Lead immediately.
   - IT Lead triggers `POST /api/v1/users/{user_id}/revoke-sessions` and flags device for `REMOTE_WIPE`.
2. Device action upon network contact:
   - Clears local SQLite database.
   - Clears secure storage keychain keys.
   - Redirects to initial setup screen.
