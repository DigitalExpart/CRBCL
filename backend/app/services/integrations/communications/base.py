"""Abstract Base Provider for Public Communications (Social Integration Foundation)."""

from abc import ABC, abstractmethod
from typing import Any


class SocialProvider(ABC):
    """Abstract interface defining Social / Public Outreach capabilities."""

    @abstractmethod
    async def publish_post(self, title: str, content: str) -> dict[str, Any]:
        """Publish public announcement to social platform."""
        pass

    @abstractmethod
    async def get_engagement_metrics(self, external_post_id: str) -> dict[str, Any]:
        """Retrieve public post analytics (impressions, shares)."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Run health check against social network API."""
        pass
