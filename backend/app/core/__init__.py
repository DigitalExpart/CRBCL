"""
CRBCL Platform — Application Configuration.

Typed settings loaded from environment variables via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "CRBCL Platform"
    app_debug: bool = False

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://crbcl:crbcl_dev_password@localhost:5432/crbcl"
    database_sync_url: str = "postgresql://crbcl:crbcl_dev_password@localhost:5432/crbcl"

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Frontend ─────────────────────────────────────────────
    frontend_url: str = "https://genserver.online"

    # ── Session / Auth ───────────────────────────────────────
    session_secret: str = "CHANGE-ME-generate-a-64-char-random-string"
    access_token_ttl: int = Field(default=86400, description="Access token TTL in seconds (default 24h)")
    refresh_token_ttl: int = Field(default=604800, description="Refresh token TTL in seconds (default 7 days)")

    # ── CORS ─────────────────────────────────────────────────
    cors_allowed_origins: str = "https://genserver.online,https://www.genserver.online,https://crbcl-sofware.vercel.app,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    # ── Object Storage ───────────────────────────────────────
    object_storage_provider: Literal["local", "s3"] = "local"
    object_storage_endpoint: str = ""
    object_storage_bucket: str = "crbcl-documents"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""

    # ── Demo Mode ────────────────────────────────────────────
    demo_mode: bool = False

    # ── Email Delivery (SMTP / Resend / Console) ─────────────
    email_provider: Literal["console", "smtp", "resend", "none"] = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = "noreply@crbcl.ca"
    smtp_from_name: str = "Chief Red Bear Children's Lodge"
    resend_api_key: str = ""

    # ── Derived helpers ──────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor — cached after first call."""
    return Settings()
