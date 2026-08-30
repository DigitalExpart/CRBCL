"""Health check endpoint with database and redis readiness."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health and readiness check."""
    status_report = {
        "status": "healthy",
        "app": "CRBCL Platform",
        "database": "unknown",
        "redis": "unknown",
    }

    # 1. Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        status_report["database"] = "ready"
    except Exception:
        status_report["database"] = "unavailable"
        status_report["status"] = "degraded"

    # 2. Check Redis
    settings = get_settings()
    try:
        redis = Redis.from_url(settings.redis_url, socket_timeout=2.0)
        await redis.ping()
        await redis.aclose()
        status_report["redis"] = "ready"
    except Exception:
        status_report["redis"] = "unavailable"
        status_report["status"] = "degraded"

    return status_report
