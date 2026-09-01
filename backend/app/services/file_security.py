"""File Security Guard enforcing signed access tokens, short expiry, MIME safety, and malware quarantine."""

import hmac
import time
import uuid

SECRET_KEY = "crbcl-file-signing-key-internal"
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def generate_signed_file_url(file_id: uuid.UUID, expiry_seconds: int = 900) -> str:
    """Generate a short-lived signed access URL (default 15 minutes)."""
    expires_at = int(time.time()) + expiry_seconds
    signature_base = f"{file_id}:{expires_at}"
    sig = hmac.new(SECRET_KEY.encode(), signature_base.encode(), "sha256").hexdigest()
    return f"/api/v1/documents/{file_id}/download?expires={expires_at}&sig={sig}"


def verify_file_signature(file_id: uuid.UUID, expires_at: int, sig: str) -> bool:
    """Verify signed document download URL signature and expiration."""
    if time.time() > expires_at:
        return False  # Expired

    expected_base = f"{file_id}:{expires_at}"
    expected_sig = hmac.new(SECRET_KEY.encode(), expected_base.encode(), "sha256").hexdigest()
    return hmac.compare_digest(expected_sig, sig)


def validate_file_upload(file_name: str, content_type: str, file_size_bytes: int) -> dict[str, str]:
    """Validate MIME type and maximum file size (50MB)."""
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Content type '{content_type}' is not permitted.")

    if file_size_bytes > 52428800:  # 50MB
        raise ValueError("File size exceeds maximum threshold of 50MB.")

    content_disposition = "attachment" if content_type == "application/pdf" else "inline"
    return {
        "status": "QUARANTINED_UNSCANNED",
        "content_disposition": f'{content_disposition}; filename="{file_name}"',
    }
