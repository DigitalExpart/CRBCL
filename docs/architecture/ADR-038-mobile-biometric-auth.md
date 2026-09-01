# ADR-038: Mobile Biometric Authentication & Encrypted Offline Storage

## Status
Approved

## Context
Mobile field devices carried into client homes or remote areas carry elevated risk of physical loss, theft, or unauthorized access. Because offline functionality requires caching sensitive child welfare data locally on the device, robust local encryption and authentication mechanisms are mandatory.

## Decision
We enforce **Local Encrypted SQLite Storage (SQLCipher / Encrypted Storage)** combined with **PIN / Biometric Quick Unlock**.

### Security Rules:
1. **Encrypted Local Storage**:
   - The local SQLite database is encrypted at rest using AES-256.
   - The encryption key is stored securely in the device's hardware-backed keystore (`flutter_secure_storage` / iOS Keychain / Android KeyStore).
2. **Offline Unlock & Token Lifecycle**:
   - Initial authentication requires full credentials (Email + Password + TOTP MFA) against the central API.
   - Upon successful online authentication, a secure 4-to-6 digit PIN or Biometric credential (Face ID / Touch ID / Fingerprint) is enrolled locally.
   - Offline app access requires PIN or Biometric unlock. Full re-authentication against the central server is required every 7 days.
3. **Inactivity & Remote Wipe**:
   - The app automatically locks after 5 minutes of inactivity.
   - If a device is reported lost or stolen, a `REMOTE_WIPE` command flag is issued on the central server. The next time the device touches any network, the local SQLite database and cached credentials are instantly purged.
   - Local database automatically purges after 14 consecutive days without server contact.

## Consequences
- Physical device loss does not expose cached child welfare records.
- Caseworkers benefit from fast PIN/Biometric unlock while in the field.
