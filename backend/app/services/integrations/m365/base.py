"""Abstract Base Provider for Microsoft 365 / Graph Integration."""

from abc import ABC, abstractmethod
from typing import Any


class MicrosoftProvider(ABC):
    """Abstract interface defining Microsoft 365 Graph capabilities."""

    @abstractmethod
    async def create_calendar_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create outbound event on external Microsoft Outlook calendar."""
        pass

    @abstractmethod
    async def update_calendar_event(self, external_id: str, event_data: dict[str, Any]) -> dict[str, Any]:
        """Update existing outbound event on Microsoft Outlook calendar."""
        pass

    @abstractmethod
    async def delete_calendar_event(self, external_id: str) -> bool:
        """Cancel/Delete outbound event on Microsoft Outlook calendar."""
        pass

    @abstractmethod
    async def send_teams_notification(self, channel_id: str, message_text: str) -> dict[str, Any]:
        """Post notification message to Microsoft Teams channel."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Run health diagnostic check against Graph API."""
        pass
