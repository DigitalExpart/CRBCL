# CRBCL Mobile Application Security Architecture

## 1. Local Database Encryption (SQLCipher AES-256)

- **Storage Engine**: `sqflite_sqlcipher` with full AES-256 page-level database encryption.
- **Key Storage**: Crypto-random 256-bit keys are generated per installation and stored using OS secure-storage facilities (`FlutterSecureStorage`), with hardware-backed protection where provided and configured by the target platform/device (iOS Keychain / Android KeyStore).
- **Backup Exclusions**: Android `AndroidManifest.xml` enforces `android:allowBackup="false"` and `android:fullBackupContent="false"`. Encryption keys are excluded from OS cloud backups, ensuring keys are never restored independently of encrypted database files.

---

## 2. Local PIN Derivation & PBKDF2 Benchmarking Strategy

- **PBKDF2 Per-Installation Key Derivation**: Low-entropy 4-6 digit PINs are processed using PBKDF2 with HMAC-SHA256 over a **cryptographically random 256-bit per-installation salt** (`crbcl_pin_salt`) stored in `FlutterSecureStorage`.
- **Iteration Benchmark Threshold**:
  - Baseline development: 100,000 iterations.
  - Production recommendation: Hardware-benchmarked target iteration count delivering **100ms–250ms derivation latency** on target ARM handheld devices (typically 210,000 to 600,000 iterations per OWASP Password Storage Guidelines).
- **Attempt Threshold & Persistent Lockout**: 5 consecutive invalid PIN attempts trigger a mandatory **15-minute lockout backoff**.
- **Lockout Persistence Across Restarts**: Failed attempt counters (`crbcl_pin_failed_attempts`) and lockout expiry timestamps (`crbcl_pin_locked_until`) are persisted in `FlutterSecureStorage`. Force-closing or restarting the application does NOT bypass the 15-minute lockout.
- **Session Re-Authentication**: Full online re-authentication (password + MFA) is enforced every 7 days.

---

## 3. Camera & EXIF Privacy Protection

- Captured photos are stored in app-private temporary storage (`path_provider`), bypassing public device galleries (`DCIM`).
- Image EXIF metadata (GPS location tags, camera serial numbers) is stripped prior to upload using `ImageSecurityHelper.stripExifMetadata()`.
- Uploaded files are deleted from local cache after successful sync push.
