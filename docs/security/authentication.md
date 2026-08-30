# CRBCL Authentication Architecture

## Overview
CRBCL uses native stateful authentication:

- **Password Storage**: Bcrypt hashing with random salt.
- **Access Tokens**: Short-lived JWTs (default 15 minutes) transferred via `HttpOnly`, `SameSite=Lax`, `Secure` cookies.
- **Refresh Tokens**: Long-lived random tokens (default 7 days) stored hashed in the `sessions` table.
- **Bearer Fallback**: The `Authorization: Bearer <token>` header is supported for non-browser/mobile clients.

## Security Controls
1. **No Plaintext Credential Logging**: Credentials and refresh tokens are excluded from logging.
2. **Account Lockout**: After 5 consecutive failed attempts, accounts are locked for 15 minutes.
3. **Session Revocation**:
   - Explicit `/api/v1/auth/logout` revokes the current session.
   - Password reset revokes all active sessions for that user.
4. **Inactive User Rejection**: Deactivated users are blocked at the authentication dependency.
