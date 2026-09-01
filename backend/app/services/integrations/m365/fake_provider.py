"""Synthetic Fake Microsoft 365 Provider for Offline Development & Testing."""

import uuid
from typing import Any

from app.services.integrations.m365.base import MicrosoftProvider


class FakeMicrosoftProvider(MicrosoftProvider):
    """Synthetic M365 provider operating entirely in-memory."""

    def __init__(self, fail_mode: bool = False):
        self.fail_mode = fail_mode
        self.created_events: dict[str, dict[str, Any]] = {}
        self.sent_teams_messages: list[dict[str, Any]] = []

    async def create_calendar_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        if self.fail_mode:
            raise ConnectionError("Simulated Microsoft Graph service outage")

        ext_id = f"fake-m365-evt-{uuid.uuid4().hex[:8]}"
        record = {
            "id": ext_id,
            "subject": event_data.get("subject", "CRBCL Appointment"),
            "body": event_data.get("body", ""),
            "start": event_data.get("start"),
            "end": event_data.get("end"),
            "etag": f'W/"fake-etag-{uuid.uuid4().hex[:6]}"',
            "status": "CREATED",
        }
        self.created_events[ext_id] = record
        return record

    async def update_calendar_event(self, external_id: str, event_data: dict[str, Any]) -> dict[str, Any]:
        if self.fail_mode:
            raise ConnectionError("Simulated Microsoft Graph service outage")

        if external_id not in self.created_events:
            # Simulate upsert/resync
            self.created_events[external_id] = {"id": external_id}

        record = self.created_events[external_id]
        record["subject"] = event_data.get("subject", record.get("subject"))
        record["body"] = event_data.get("body", record.get("body"))
        record["etag"] = f'W/"fake-etag-updated-{uuid.uuid4().hex[:6]}"'
        record["status"] = "UPDATED"
        return record

    async def delete_calendar_event(self, external_id: str) -> bool:
        if self.fail_mode:
            raise ConnectionError("Simulated Microsoft Graph service outage")
        if external_id in self.created_events:
            del self.created_events[external_id]
        return True

    async def send_teams_notification(self, channel_id: str, message_text: str) -> dict[str, Any]:
        if self.fail_mode:
            raise ConnectionError("Simulated Microsoft Graph service outage")
        msg_id = f"fake-teams-msg-{uuid.uuid4().hex[:8]}"
        record = {"id": msg_id, "channel_id": channel_id, "content": message_text}
        self.sent_teams_messages.append(record)
        return record

    async def health_check(self) -> dict[str, Any]:
        if self.fail_mode:
            return {"status": "ERROR", "message": "Graph API unreachable"}
        return {"status": "OK", "provider": "FakeMicrosoftProvider", "latency_ms": 12}
