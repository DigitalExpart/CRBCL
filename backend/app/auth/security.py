"""JWT creation, verification, cookie configuration, password hashing, and CSRF protection."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (), {"__version__": getattr(bcrypt, "__version__", "4.0.0")})()

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# ── Password hashing ────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token helpers ────────────────────────────────────────────

ALGORITHM = "HS256"


def create_access_token(user_id: uuid.UUID, extra: dict | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.session_secret, algorithm=ALGORITHM)


def create_refresh_token() -> str:
    """Generate a random refresh token string."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash of the refresh token for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_reset_token(user_id: uuid.UUID) -> str:
    """Generate a signed, 1-hour password reset JWT token."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=1),
        "type": "password_reset",
    }
    return jwt.encode(payload, settings.session_secret, algorithm=ALGORITHM)


def decode_reset_token(token: str) -> uuid.UUID | None:
    """Validate a password reset token and return the user UUID."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None


# ── CSRF Token helpers ──────────────────────────────────────


def generate_csrf_token() -> str:
    """Generate cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token_from_header: str | None, token_from_cookie: str | None) -> bool:
    """Verify CSRF token using constant-time comparison."""
    if not token_from_header or not token_from_cookie:
        return False
    return secrets.compare_digest(token_from_header, token_from_cookie)


# ── Cookie configuration ────────────────────────────────────


def get_cookie_settings(is_csrf: bool = False) -> dict:
    settings = get_settings()
    return {
        "httponly": not is_csrf,  # CSRF token cookie is readable by frontend client
        "secure": True,
        "samesite": "none" if settings.is_production else "lax",
        "path": "/",
        "domain": None,
    }
