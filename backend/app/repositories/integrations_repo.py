"""Enterprise Integrations Repository for CRBCL (Phase 13)."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import (
    AiRequestAudit,
    CommunicationsPost,
    IntegrationExternalLink,
    IntegrationRegistry,
    OcrJob,
)


class IntegrationsRepository:
    """Database persistence operations for Integrations, M365, OCR, AI & Communications."""

    # ── 1. Integrations Registry ──────────────────────────────────────
    @staticmethod
    async def get_integrations(session: AsyncSession) -> list[IntegrationRegistry]:
        """Fetch all third-party integration provider records."""
        stmt = select(IntegrationRegistry).order_by(IntegrationRegistry.display_name)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_integration_by_key(session: AsyncSession, provider_key: str) -> IntegrationRegistry | None:
        """Fetch integration configuration record by key (e.g., MICROSOFT, AI, OCR)."""
        stmt = select(IntegrationRegistry).where(IntegrationRegistry.provider_key == provider_key)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_integration(
        session: AsyncSession, integration: IntegrationRegistry, data: dict[str, Any]
    ) -> IntegrationRegistry:
        """Update integration enablement or status metadata."""
        for key, value in data.items():
            if hasattr(integration, key):
                setattr(integration, key, value)
        await session.flush()
        return integration

    # ── 2. External Links (Idempotency Mapping) ───────────────────────
    @staticmethod
    async def create_external_link(session: AsyncSession, link_data: dict[str, Any]) -> IntegrationExternalLink:
        """Create mapping between internal CRBCL entity and external provider ID."""
        obj = IntegrationExternalLink(**link_data)
        session.add(obj)
        await session.flush()
        return obj

    @staticmethod
    async def get_external_link(
        session: AsyncSession, provider_key: str, entity_type: str, internal_entity_id: uuid.UUID
    ) -> IntegrationExternalLink | None:
        """Retrieve external mapping by internal entity ID."""
        stmt = select(IntegrationExternalLink).where(
            IntegrationExternalLink.provider_key == provider_key,
            IntegrationExternalLink.entity_type == entity_type,
            IntegrationExternalLink.internal_entity_id == internal_entity_id,
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    # ── 3. OCR Document Jobs ──────────────────────────────────────────
    @staticmethod
    async def create_ocr_job(session: AsyncSession, job_data: dict[str, Any]) -> OcrJob:
        """Create a new OCR processing job record."""
        obj = OcrJob(**job_data)
        session.add(obj)
        await session.flush()
        return obj

    @staticmethod
    async def get_ocr_job(session: AsyncSession, job_id: uuid.UUID) -> OcrJob | None:
        """Fetch OCR job by ID."""
        stmt = select(OcrJob).where(OcrJob.id == job_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_ocr_job(session: AsyncSession, job: OcrJob, data: dict[str, Any]) -> OcrJob:
        """Update OCR job status or candidate fields."""
        for key, value in data.items():
            if hasattr(job, key):
                setattr(job, key, value)
        await session.flush()
        return job

    # ── 4. AI Audit & Usage ───────────────────────────────────────────
    @staticmethod
    async def log_ai_request_audit(session: AsyncSession, audit_data: dict[str, Any]) -> AiRequestAudit:
        """Log AI request metadata, tokens, and intent for audit compliance."""
        obj = AiRequestAudit(**audit_data)
        session.add(obj)
        await session.flush()
        return obj

    # ── 5. Communications Posts (Social Foundation) ───────────────────
    @staticmethod
    async def create_communications_post(session: AsyncSession, post_data: dict[str, Any]) -> CommunicationsPost:
        """Create public communications draft post."""
        obj = CommunicationsPost(**post_data)
        session.add(obj)
        await session.flush()
        return obj

    @staticmethod
    async def get_communications_posts(
        session: AsyncSession, status_filter: str | None = None
    ) -> list[CommunicationsPost]:
        """List public outreach posts."""
        stmt = select(CommunicationsPost).order_by(CommunicationsPost.created_at.desc())
        if status_filter:
            stmt = stmt.where(CommunicationsPost.status == status_filter)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_communications_post_by_id(session: AsyncSession, post_id: uuid.UUID) -> CommunicationsPost | None:
        """Fetch communications post by ID."""
        stmt = select(CommunicationsPost).where(CommunicationsPost.id == post_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_communications_post(
        session: AsyncSession, post: CommunicationsPost, data: dict[str, Any]
    ) -> CommunicationsPost:
        """Update communications post status or approval."""
        for key, value in data.items():
            if hasattr(post, key):
                setattr(post, key, value)
        await session.flush()
        return post
