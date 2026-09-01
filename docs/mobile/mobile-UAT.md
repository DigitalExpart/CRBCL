# CRBCL Mobile Application UAT & Pilot Verification Checklist

| Scenario # | User Action | Expected System Behavior | Pass/Fail Criteria |
| :--- | :--- | :--- | :--- |
| **UAT-MOB-01** | First-time online login | App registers device via `POST /sync/devices/register` and prompts for PIN setup. | Device status ACTIVE; PIN hash stored. |
| **UAT-MOB-02** | Enter 5 incorrect PINs | App triggers 15-minute lockout backoff timer. | PIN input disabled for 15 minutes. |
| **UAT-MOB-03** | Pull sync in online mode | Assigned cases downloaded to encrypted SQLite storage. | Authorized cases available offline. |
| **UAT-MOB-04** | Draft Case Note offline | Note saved to local SQLite `sync_queue` outbox with client mutation UUID. | Outbox status PENDING [1 item]. |
| **UAT-MOB-05** | Reconnect to network | `SyncEngine` pushes batch outbox queue to `POST /sync/push`. | Server creates CaseNote; outbox cleared. |
| **UAT-MOB-06** | Push duplicate mutation ID | Server returns `ALREADY_PROCESSED`. | No duplicate Case Note created. |
| **UAT-MOB-07** | Case access revoked on server | Next pull sync returns tombstone for revoked Case ID. | Case removed from mobile SQLite database. |
| **UAT-MOB-08** | Admin revokes device | Server returns HTTP 403 `DEVICE_REVOKED` on sync push/pull. | App purges local database and keys. |
