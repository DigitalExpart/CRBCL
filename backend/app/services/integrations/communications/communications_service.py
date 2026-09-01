"""Public Communications Service (Social Media Integration Foundation)."""

import logging
import uuid
from datetime import datetime
from typing import Any

from app.models.integrations import CommunicationsPost
from app.services.integrations.communications.base import SocialProvider
from app.services.integrations.communications.fake_provider import FakeSocialProvider
from app.services.integrations.utils import db_commit, db_query_first, db_refresh

logger = logging.getLogger(__name__)


async def create_communications_post(
    db: Any,
    title: str,
    content: str,
    created_by_id: uuid.UUID,
    target_platforms: str = "META",
) -> CommunicationsPost:
    """Create a new public communications outreach post in DRAFT status."""
    post = CommunicationsPost(
        title=title,
        content=content,
        created_by_id=created_by_id,
        target_platforms=target_platforms,
        status="DRAFT",
    )
    db.add(post)
    await db_commit(db)
    await db_refresh(db, post)
    return post


async def approve_communications_post(db: Any, post_id: uuid.UUID, approved_by_id: uuid.UUID) -> CommunicationsPost:
    """Approve a public communications post for publication."""
    post = await db_query_first(db, CommunicationsPost, CommunicationsPost.id == post_id)
    if not post:
        raise ValueError(f"Communications post {post_id} not found.")

    post.status = "APPROVED"
    post.approved_by_id = approved_by_id
    post.updated_at = datetime.utcnow()
    await db_commit(db)
    await db_refresh(db, post)
    return post


async def publish_communications_post(
    db: Any,
    post_id: uuid.UUID,
    provider: SocialProvider | None = None,
) -> dict[str, Any]:
    """Publish an approved public post to configured social network."""
    post = await db_query_first(db, CommunicationsPost, CommunicationsPost.id == post_id)
    if not post:
        raise ValueError(f"Communications post {post_id} not found.")

    if post.status != "APPROVED":
        raise ValueError(f"Communications post must be APPROVED prior to publication (current: {post.status}).")

    if provider is None:
        provider = FakeSocialProvider()

    res = await provider.publish_post(post.title, post.content)

    post.status = "PUBLISHED"
    post.published_at = datetime.utcnow()
    post.updated_at = datetime.utcnow()
    await db_commit(db)

    return {"status": "PUBLISHED", "external_post_id": res.get("external_post_id")}
