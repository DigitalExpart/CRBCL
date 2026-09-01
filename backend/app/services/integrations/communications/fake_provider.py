"""Synthetic Fake Social Provider for Public Communications testing."""

import uuid
from typing import Any

from app.services.integrations.communications.base import SocialProvider


class FakeSocialProvider(SocialProvider):
    """Synthetic social network provider."""

    def __init__(self, fail_mode: bool = False):
        self.fail_mode = fail_mode

    async def publish_post(self, title: str, content: str) -> dict[str, Any]:
        if self.fail_mode:
            raise RuntimeError("Social API connection error")
        return {
            "external_post_id": f"fake-social-{uuid.uuid4().hex[:8]}",
            "status": "PUBLISHED",
            "platform": "META",
        }

    async def get_engagement_metrics(self, external_post_id: str) -> dict[str, Any]:
        if self.fail_mode:
            raise RuntimeError("Social API connection error")
        return {"views": 450, "shares": 18, "likes": 64}

    async def health_check(self) -> dict[str, Any]:
        if self.fail_mode:
            return {"status": "ERROR", "message": "Social network API down"}
        return {"status": "OK", "provider": "FakeSocialProvider"}
