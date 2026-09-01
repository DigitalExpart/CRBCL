# CRBCL Mobile Field Application Operations Guide

## 1. Environment & API Endpoint Configuration

The mobile app supports environment-specific configuration targeting local development, staging, or production cloud gateways:

```dart
class AppConfig {
  static const String baseUrl = String.fromEnvironment(
    'CRBCL_API_BASE_URL',
    defaultValue: 'https://api.crbcl.ca', // Explicit production gateway URL
  );
}
```

---

## 2. Device Registration & Provisioning Workflow

1. Caseworker installs the CRBCL Field App on an IT-provisioned handheld device.
2. Caseworker logs in online with full credentials (`email`, `password`, `TOTP MFA`).
3. App invokes `POST /api/v1/sync/devices/register` with unique hardware `device_id`.
4. Server creates a `MobileDevice` row with status `ACTIVE`.
5. Caseworker sets up a 4 or 6-digit PIN for offline vault access.

---

## 3. Remote Device Revocation & Wipe Protocol

- **Administrator Action**: When a device is reported lost/stolen, an IT Admin invokes `POST /api/v1/sync/devices/{device_id}/revoke`.
- **Enforcement**: Any subsequent `/pull` or `/push` request with header `X-Device-ID: {device_id}` receives HTTP 403 `DEVICE_REVOKED`.
- **Client Action**: Upon receiving `DEVICE_REVOKED`, the mobile app automatically calls `LocalDatabaseHelper.instance.purgeDatabase()`, clearing the SQLCipher database, secure storage keys, and cached credentials.
