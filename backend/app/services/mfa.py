"""Multi-Factor Authentication (MFA / TOTP) Service."""

import base64
import hashlib
import hmac
import os
import struct
import time


def generate_mfa_secret() -> str:
    """Generate a crypto-random Base32 TOTP secret."""
    raw = os.urandom(20)
    return base64.b32encode(raw).decode("utf-8").rstrip("=")


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate deterministic random alphanumeric single-use recovery codes."""
    codes = []
    for _ in range(count):
        code = os.urandom(5).hex().upper()
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify a 6-digit TOTP code against a Base32 secret with a drift window."""
    if not secret or not code or len(code) != 6 or not code.isdigit():
        return False

    # Pad Base32 secret
    padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
    try:
        key = base64.b32decode(padded_secret, casefold=True)
    except Exception:
        return False

    current_interval = int(time.time() // 30)

    for offset in range(-window, window + 1):
        interval = current_interval + offset
        msg = struct.pack(">Q", interval)
        hmac_digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset_idx = hmac_digest[-1] & 0x0F
        truncated_hash = struct.unpack(">I", hmac_digest[offset_idx : offset_idx + 4])[0] & 0x7FFFFFFF
        computed_code = str(truncated_hash % 1000000).zfill(6)

        if hmac.compare_digest(computed_code, code):
            return True

    return False
