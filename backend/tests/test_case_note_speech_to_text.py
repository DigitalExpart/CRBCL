"""Comprehensive tests for Secure Speech-to-Text Case Note Transcription.

CRBCL Security & Privacy Requirements:
1. Unauthorized user receives 401/403.
2. User without Case Note capability receives 403.
3. IT Admin does not gain Case Note transcription/content authority merely through IT role.
4. Office Coordinator receives 403.
5. Front Desk receives 403 unless independently authorized.
6. Authorized Case Note staff can invoke transcription when feature is enabled.
7. Feature disabled returns safe unavailable response (503).
8. Empty audio rejected (400).
9. Unsupported content type rejected (415).
10. Oversized payload rejected (413).
11. Fake provider returns synthetic transcript in tests.
12. Transcription endpoint does NOT create a Case Note.
13. Transcription endpoint does NOT update/finalize a Case Note.
14. Raw audio is not persisted anywhere in storage or database.
15. Audit/log data does not contain transcript content.
"""

from __future__ import annotations

import io
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core import get_settings
from app.models.audit import AuditEvent
from app.models.case_note import CaseNote
from app.models.role import Role, UserRole
from app.models.user import User


@pytest.fixture
async def sample_case(client: AsyncClient, caseworker_user: dict) -> str:
    """Create a sample case for speech-to-text tests."""
    res = await client.post(
        "/api/v1/cases",
        json={"title": "Synthetic Test Case for Speech", "case_type": "Child Safety", "status": "Open"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.fixture
async def front_desk_user(db_session: AsyncSession, seed_roles_and_permissions: dict) -> dict:
    """Create a pure Front Desk worker user without Case Note capabilities."""
    res = await db_session.execute(select(Role).where(Role.key == "front_desk"))
    fd_role = res.scalars().first()
    if not fd_role:
        fd_role = Role(key="front_desk", name="Front Desk / Reception", is_system=False)
        db_session.add(fd_role)
        await db_session.flush()

    user = User(
        email="frontdesk_worker@crbcl.ca",
        email_normalized="frontdesk_worker@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Faith FrontDesk",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=fd_role.id))
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.mark.asyncio
async def test_01_unauthorized_user_denied(client: AsyncClient, sample_case: str):
    """Scenario 1: Unauthenticated request receives 401 Unauthorized."""
    audio_file = ("audio.webm", io.BytesIO(b"RIFFdummydata"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
    )
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_02_user_without_case_note_capability_denied(
    client: AsyncClient,
    sample_case: str,
    navigator_user: dict,
):
    """Scenario 2: User lacking CASE_NOTE_CREATE capability receives 403 Forbidden."""
    audio_file = ("audio.webm", io.BytesIO(b"synthetic audio content"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=navigator_user["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_03_it_admin_cannot_access_case_note_transcription(
    client: AsyncClient,
    sample_case: str,
    it_admin_user: dict,
):
    """Scenario 3: IT Admin does NOT gain Case Note transcription authority through technical role."""
    audio_file = ("audio.webm", io.BytesIO(b"synthetic audio content"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=it_admin_user["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_04_office_coordinator_denied(
    client: AsyncClient,
    sample_case: str,
    office_coordinator_user: dict,
):
    """Scenario 4: Office Coordinator receives 403 Forbidden on Case Note transcription."""
    audio_file = ("audio.webm", io.BytesIO(b"synthetic audio content"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=office_coordinator_user["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_05_front_desk_denied(
    client: AsyncClient,
    sample_case: str,
    front_desk_user: dict,
):
    """Scenario 5: Pure Front Desk worker receives 403 Forbidden."""
    audio_file = ("audio.webm", io.BytesIO(b"synthetic audio content"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=front_desk_user["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_06_and_11_authorized_staff_can_transcribe_with_fake_provider(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 6 & 11: Authorized staff receives synthetic transcript from configured test provider."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    audio_file = ("note.webm", io.BytesIO(b"synthetic test audio bytes"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"language": "en"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert "transcript" in data
    assert data["transcript"] == "This is a synthetic test case note."
    assert data["provider"] == "fake"
    assert res.headers.get("cache-control") == "no-store, private"


@pytest.mark.asyncio
async def test_07_feature_disabled_returns_503(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 7: When speech-to-text is disabled, returns safe 503 unavailable response."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", False)
    monkeypatch.setattr(settings, "speech_provider", "disabled")

    audio_file = ("note.webm", io.BytesIO(b"synthetic test audio bytes"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 503
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code in ("SPEECH_TRANSCRIPTION_DISABLED", "SPEECH_PROVIDER_NOT_CONFIGURED")


@pytest.mark.asyncio
async def test_08_empty_audio_rejected(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 8: Empty audio (0 bytes) is rejected with 400 Bad Request."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    empty_audio = ("empty.webm", io.BytesIO(b""), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": empty_audio},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 400
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "EMPTY_AUDIO"


@pytest.mark.asyncio
async def test_09_unsupported_content_type_rejected(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 9: Unsupported content types (e.g. application/pdf, text/plain) are rejected with 415."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    invalid_file = ("document.pdf", io.BytesIO(b"%PDF-1.4 synthetic content"), "application/pdf")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": invalid_file},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 415
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "UNSUPPORTED_AUDIO_FORMAT"


@pytest.mark.asyncio
async def test_10_oversized_payload_rejected(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 10: Payload exceeding technical limit is rejected with 413 Payload Too Large."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")
    monkeypatch.setattr(settings, "speech_max_file_size_bytes", 1024)  # Small limit for testing

    oversized = ("huge.webm", io.BytesIO(b"x" * 2048), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": oversized},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 413
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "AUDIO_TOO_LARGE"


@pytest.mark.asyncio
async def test_12_and_13_transcription_does_not_mutate_case_notes(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    db_session: AsyncSession,
    monkeypatch,
):
    """Scenario 12 & 13: Transcription endpoint does NOT create, update, or finalize any CaseNote."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    # Count notes before
    case_uuid = uuid.UUID(sample_case)
    notes_before_stmt = select(func.count(CaseNote.id)).where(CaseNote.case_id == case_uuid)
    count_before = (await db_session.execute(notes_before_stmt)).scalar()

    audio_file = ("note.webm", io.BytesIO(b"synthetic audio content"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200

    # Count notes after - MUST BE IDENTICAL (transcription is input-assist only)
    count_after = (await db_session.execute(notes_before_stmt)).scalar()
    assert count_after == count_before, "Transcription endpoint must NEVER create a CaseNote record!"


@pytest.mark.asyncio
async def test_14_and_15_raw_audio_and_transcript_not_persisted_in_audit_logs(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    db_session: AsyncSession,
    monkeypatch,
):
    """Scenario 14 & 15: Zero persistence of raw audio and transcript narrative in audit tables."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    audio_payload = b"UNIQUE_RAW_AUDIO_BYTE_SEQUENCE_FOR_TESTING"
    audio_file = ("note.webm", io.BytesIO(audio_payload), "audio/webm")

    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200
    transcript_text = res.json()["transcript"]

    # Check AuditEvent table: metadata must be safe, no narrative content
    case_uuid = uuid.UUID(sample_case)
    audit_stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "case",
            AuditEvent.entity_id == case_uuid,
            AuditEvent.event_type == "speech_transcription_succeeded",
        )
        .order_by(AuditEvent.timestamp.desc())
    )
    audit_event = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit_event is not None

    meta = getattr(audit_event, "metadata_", None) or {}
    meta_str = str(meta).lower()

    # Verify no raw audio bytes stored
    assert "unique_raw_audio" not in meta_str
    # Verify no transcript narrative stored
    assert transcript_text.lower() not in meta_str
    # Verify safe metadata exists
    assert meta.get("provider") == "fake"
    assert meta.get("outcome") == "success"
    assert meta.get("audio_bytes_length") == len(audio_payload)


@pytest.mark.asyncio
async def test_transcription_status_endpoint(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Verify GET /cases/{case_id}/notes/transcribe/status returns current configuration."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    res = await client.get(
        f"/api/v1/cases/{sample_case}/notes/transcribe/status",
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is True
    assert data["provider"] == "fake"
    assert data["available"] is True
    assert "max_file_size_bytes" in data
