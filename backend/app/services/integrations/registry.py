"""Integration Registry and Administrative Health Inspection Service."""

import json
from datetime import datetime
from typing import Any

from app.models.integrations import IntegrationRegistry
from app.services.integrations.utils import db_commit, db_query_all, db_query_first, db_refresh

DEFAULT_INTEGRATION_PROVIDERS = [
    {
        "provider_key": "M365",
        "display_name": "Microsoft 365 / Graph (Outlook & Teams)",
        "category": "M365",
        "status": "DISABLED",
        "is_enabled": False,
        "is_approved": False,
        "config_metadata": json.dumps({"tenant_type": "SINGLE_TENANT", "scopes": ["Calendars.ReadWrite"]}),
    },
    {
        "provider_key": "AI_RED_BEAR",
        "display_name": "Ask Red Bear Assistive AI (Anthropic)",
        "category": "AI",
        "status": "DISABLED",
        "is_enabled": False,
        "is_approved": False,
        "config_metadata": json.dumps({"model": "claude-3-5-sonnet", "max_tokens": 1024}),
    },
    {
        "provider_key": "OCR_TESSERACT",
        "display_name": "Document OCR Engine",
        "category": "OCR",
        "status": "DISABLED",
        "is_enabled": False,
        "is_approved": False,
        "config_metadata": json.dumps({"engine": "Tesseract", "allowed_mimetypes": ["application/pdf", "image/png"]}),
    },
    {
        "provider_key": "TELEMATICS_SAMSARA",
        "display_name": "Fleet GPS & Telematics Provider",
        "category": "TELEMATICS",
        "status": "DISABLED",
        "is_enabled": False,
        "is_approved": False,
        "config_metadata": json.dumps({"update_frequency_seconds": 60}),
    },
    {
        "provider_key": "SOCIAL_META",
        "display_name": "Public Communications (Meta / X)",
        "category": "SOCIAL",
        "status": "DISABLED",
        "is_enabled": False,
        "is_approved": False,
        "config_metadata": json.dumps({"approval_required": True}),
    },
]


async def ensure_default_integrations_seeded(db: Any) -> None:
    """Ensure baseline integration registry records exist in database."""
    for item in DEFAULT_INTEGRATION_PROVIDERS:
        existing = await db_query_first(
            db, IntegrationRegistry, IntegrationRegistry.provider_key == item["provider_key"]
        )
        if not existing:
            reg = IntegrationRegistry(
                provider_key=item["provider_key"],
                display_name=item["display_name"],
                category=item["category"],
                status=item["status"],
                is_enabled=item["is_enabled"],
                is_approved=item["is_approved"],
                config_metadata=item["config_metadata"],
            )
            db.add(reg)
    await db_commit(db)


async def get_all_integrations_health(db: Any) -> list[dict[str, Any]]:
    """Return administrative health and status matrix without exposing secret values."""
    await ensure_default_integrations_seeded(db)
    records = await db_query_all(db, IntegrationRegistry)
    results = []
    for r in records:
        results.append(
            {
                "id": str(r.id),
                "provider_key": r.provider_key,
                "display_name": r.display_name,
                "category": r.category,
                "status": r.status,
                "is_enabled": r.is_enabled,
                "is_approved": r.is_approved,
                "last_health_check_at": r.last_health_check_at.isoformat() if r.last_health_check_at else None,
                "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None,
                "last_error": r.last_error,
                "config_summary": json.loads(r.config_metadata) if r.config_metadata else {},
            }
        )
    return results


async def update_integration_status(
    db: Any, provider_key: str, is_enabled: bool, is_approved: bool, status: str
) -> IntegrationRegistry:
    """Update integration configuration state."""
    await ensure_default_integrations_seeded(db)
    record = await db_query_first(db, IntegrationRegistry, IntegrationRegistry.provider_key == provider_key)
    if not record:
        raise ValueError(f"Integration provider '{provider_key}' not found.")

    record.is_enabled = is_enabled
    record.is_approved = is_approved
    record.status = status
    record.updated_at = datetime.utcnow()
    await db_commit(db)
    await db_refresh(db, record)
    return record
