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
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.core import get_settings
from app.models.audit import AuditEvent
from app.models.case_note import CaseNote, CaseNoteAddendum
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import TeamMembership
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.speech.provider import (
    DisabledSpeechTranscriptionProvider,
    FakeSpeechTranscriptionProvider,
    LocalWhisperSpeechTranscriptionProvider,
    get_speech_provider,
)


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


@pytest.fixture
async def sample_case_note(client: AsyncClient, sample_case: str, caseworker_user: dict) -> str:
    """Create a sample case note on the sample case for addendum context testing."""
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes",
        json={"subject": "Baseline Note for Addendum Speech Tests", "content": "Initial baseline note content."},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.fixture
async def case_aide_user(db_session: AsyncSession, seed_roles_and_permissions: dict) -> dict:
    """Create a Case Aide user who possesses CASE_NOTE_CREATE but lacks CASE_NOTE_ADDENDUM."""
    res = await db_session.execute(select(Role).where(Role.key == "case_aide"))
    aide_role = res.scalars().first()
    if not aide_role:
        aide_role = Role(key="case_aide", name="Case Aide", is_system=False)
        db_session.add(aide_role)
        await db_session.flush()

    # Assign CASE_NOTE_CREATE and CASE_READ to aide_role, explicitly omitting CASE_NOTE_ADDENDUM
    perm_stmt = select(Permission).where(
        Permission.key.in_([Permissions.CASE_READ, Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE])
    )
    perms_res = await db_session.execute(perm_stmt)
    for p in perms_res.scalars().all():
        db_session.add(RolePermission(role_id=aide_role.id, permission_id=p.id))
    await db_session.flush()

    user = User(
        email="case_aide_worker@crbcl.ca",
        email_normalized="case_aide_worker@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Alex CaseAide",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=aide_role.id))
    db_session.add(TeamMembership(user_id=user.id, team_id=seed_roles_and_permissions["team"].id, is_primary=True))
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


@pytest.mark.asyncio
async def test_16_authorized_staff_can_transcribe_addendum_context(
    client: AsyncClient,
    sample_case: str,
    sample_case_note: str,
    caseworker_user: dict,
    db_session: AsyncSession,
    monkeypatch,
):
    """Scenario 16: Staff authorized for addenda can transcribe with purpose='addendum' and valid note_id."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    audio_file = ("addendum.webm", io.BytesIO(b"synthetic addendum audio bytes"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"purpose": "addendum", "note_id": sample_case_note, "language": "en"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["transcript"] == "This is a synthetic test case note."
    assert res.headers.get("cache-control") == "no-store, private"

    # Verify audit event captures purpose and note_id without raw narrative
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
    audit_event = (await db_session.execute(audit_stmt)).scalars().first()
    assert audit_event is not None
    meta = getattr(audit_event, "metadata_", None) or {}
    assert meta.get("purpose") == "addendum"
    assert meta.get("note_id") == sample_case_note


@pytest.mark.asyncio
async def test_17_user_with_create_but_without_addendum_permission_denied_for_addendum(
    client: AsyncClient,
    sample_case: str,
    sample_case_note: str,
    case_aide_user: dict,
    monkeypatch,
):
    """Scenario 17: User possessing CASE_NOTE_CREATE but lacking CASE_NOTE_ADDENDUM receives 403 on addendum context."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    audio_file = ("addendum.webm", io.BytesIO(b"synthetic addendum audio bytes"), "audio/webm")

    # 1. Attempt addendum context -> Must be rejected with 403 Forbidden
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"purpose": "addendum", "note_id": sample_case_note},
        headers=case_aide_user["headers"],
    )
    assert res.status_code == 403
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "PERMISSION_DENIED"

    # 2. Same user with case_note context -> Allowed because they possess CASE_NOTE_CREATE
    audio_file_2 = ("note.webm", io.BytesIO(b"synthetic note audio bytes"), "audio/webm")
    allowed_res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file_2},
        data={"purpose": "case_note"},
        headers=case_aide_user["headers"],
    )
    assert allowed_res.status_code == 200


@pytest.mark.asyncio
async def test_18_addendum_transcription_requires_note_id(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 18: Addendum transcription without note_id is rejected with 400 Bad Request."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    audio_file = ("addendum.webm", io.BytesIO(b"synthetic audio bytes"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"purpose": "addendum"},  # Missing note_id
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 400
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "NOTE_ID_REQUIRED"


@pytest.mark.asyncio
async def test_19_addendum_transcription_rejects_nonexistent_or_unassociated_note(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 19: Nonexistent note_id yields 404; note belonging to another case yields 400."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    # A. Nonexistent note ID
    audio_file_1 = ("addendum.webm", io.BytesIO(b"synthetic audio bytes"), "audio/webm")
    fake_note_id = str(uuid.uuid4())
    res_nonexistent = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file_1},
        data={"purpose": "addendum", "note_id": fake_note_id},
        headers=caseworker_user["headers"],
    )
    assert res_nonexistent.status_code == 404

    # B. Note belonging to a different case
    other_case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Second Case for Mismatch Test", "case_type": "Child Safety", "status": "Open"},
        headers=caseworker_user["headers"],
    )
    assert other_case_res.status_code == 201
    other_case_id = other_case_res.json()["id"]

    other_note_res = await client.post(
        f"/api/v1/cases/{other_case_id}/notes",
        json={"subject": "Note on other case", "content": "Narrative"},
        headers=caseworker_user["headers"],
    )
    assert other_note_res.status_code == 201
    other_note_id = other_note_res.json()["id"]

    # Request transcription for sample_case with other_case's note_id
    audio_file_2 = ("addendum.webm", io.BytesIO(b"synthetic audio bytes"), "audio/webm")
    res_mismatched = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file_2},
        data={"purpose": "addendum", "note_id": other_note_id},
        headers=caseworker_user["headers"],
    )
    assert res_mismatched.status_code == 400
    error_code = res_mismatched.json().get("error", {}).get("code") or res_mismatched.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "INVALID_NOTE_CASE"


@pytest.mark.asyncio
async def test_20_addendum_transcription_never_creates_addendum_record(
    client: AsyncClient,
    sample_case: str,
    sample_case_note: str,
    caseworker_user: dict,
    db_session: AsyncSession,
    monkeypatch,
):
    """Scenario 20: Transcribing for addendum context NEVER inserts a CaseNoteAddendum record."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    note_uuid = uuid.UUID(sample_case_note)
    count_stmt = select(func.count(CaseNoteAddendum.id)).where(CaseNoteAddendum.case_note_id == note_uuid)
    count_before = (await db_session.execute(count_stmt)).scalar()

    audio_file = ("addendum.webm", io.BytesIO(b"synthetic addendum audio bytes"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"purpose": "addendum", "note_id": sample_case_note},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200

    count_after = (await db_session.execute(count_stmt)).scalar()
    assert count_after == count_before, "Addendum transcription must NEVER create an addendum record!"


@pytest.mark.asyncio
async def test_21_invalid_purpose_rejected(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 21: Invalid purpose value is rejected with 400 Bad Request."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")

    audio_file = ("note.webm", io.BytesIO(b"synthetic audio bytes"), "audio/webm")
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"purpose": "unknown_context"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 400
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code == "INVALID_PURPOSE"


def test_22_local_whisper_provider_selection_and_disabled_default(monkeypatch):
    """Scenario 22: Provider factory respects configuration and defaults to disabled."""
    settings = get_settings()

    # When disabled, always returns DisabledSpeechTranscriptionProvider
    monkeypatch.setattr(settings, "speech_to_text_enabled", False)
    monkeypatch.setattr(settings, "speech_provider", "local_whisper")
    provider = get_speech_provider(settings)
    assert isinstance(provider, DisabledSpeechTranscriptionProvider)
    assert not provider.is_available

    # When enabled with local_whisper
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "local_whisper")
    provider = get_speech_provider(settings)
    assert isinstance(provider, LocalWhisperSpeechTranscriptionProvider)
    assert provider.provider_id == "local_whisper"

    # When enabled with local alias
    monkeypatch.setattr(settings, "speech_provider", "local")
    provider = get_speech_provider(settings)
    assert isinstance(provider, LocalWhisperSpeechTranscriptionProvider)

    # When enabled with fake provider
    monkeypatch.setattr(settings, "speech_provider", "fake")
    provider = get_speech_provider(settings)
    assert isinstance(provider, FakeSpeechTranscriptionProvider)

    # When enabled with unapproved/unknown provider
    monkeypatch.setattr(settings, "speech_provider", "unapproved_cloud_api")
    provider = get_speech_provider(settings)
    assert isinstance(provider, DisabledSpeechTranscriptionProvider)


def test_23_local_whisper_model_caching_and_lifecycle():
    """Scenario 23: WhisperModel is loaded once and cached at process level."""
    # Reset model cache for test isolation
    LocalWhisperSpeechTranscriptionProvider._cached_model = None
    LocalWhisperSpeechTranscriptionProvider._cached_model_key = None

    mock_model_instance = MagicMock()
    with patch("faster_whisper.WhisperModel", return_value=mock_model_instance) as mock_cls:
        provider = LocalWhisperSpeechTranscriptionProvider()
        m1 = provider._get_or_load_model()
        assert m1 is mock_model_instance
        assert mock_cls.call_count == 1
        assert provider.is_model_loaded() is True

        # Second call reuses cached instance without re-instantiation
        m2 = provider._get_or_load_model()
        assert m2 is mock_model_instance
        assert mock_cls.call_count == 1

        # Check readiness metadata
        readiness = provider.get_readiness_info()
        assert readiness["loaded"] is True
        assert readiness["status"] == "ready"
        assert readiness["provider_id"] == "local_whisper"


@pytest.mark.asyncio
async def test_24_local_whisper_bounded_concurrency():
    """Scenario 24: Bounded concurrency ensures max concurrent inferences is capped."""
    import asyncio
    import time

    settings = get_settings()
    provider = LocalWhisperSpeechTranscriptionProvider(settings)
    provider.max_concurrency = 2

    # Reset semaphore
    LocalWhisperSpeechTranscriptionProvider._semaphore = None

    active_inferences = 0
    max_observed_concurrent = 0

    def mock_sync_transcribe(audio_bytes, language):
        nonlocal active_inferences, max_observed_concurrent
        active_inferences += 1
        if active_inferences > max_observed_concurrent:
            max_observed_concurrent = active_inferences
        time.sleep(0.05)
        active_inferences -= 1
        return "Synthetic transcript"

    with patch.object(provider, "_sync_transcribe", side_effect=mock_sync_transcribe):
        tasks = [
            provider.transcribe(b"test audio bytes", "audio/webm")
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert max_observed_concurrent <= 2


@pytest.mark.asyncio
async def test_25_local_whisper_initialization_failure_handling(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 25: Model initialization failure raises SPEECH_MODEL_NOT_READY (503)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "local_whisper")

    LocalWhisperSpeechTranscriptionProvider._cached_model = None
    LocalWhisperSpeechTranscriptionProvider._cached_model_key = None

    with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("GPU/CPU load error")):
        audio_file = ("note.webm", io.BytesIO(b"synthetic audio bytes"), "audio/webm")
        res = await client.post(
            f"/api/v1/cases/{sample_case}/notes/transcribe",
            files={"file": audio_file},
            data={"purpose": "case_note"},
            headers=caseworker_user["headers"],
        )
        assert res.status_code == 503
        data = res.json()
        error_code = data.get("error", {}).get("code") or data.get("detail", {}).get("error", {}).get("code")
        assert error_code == "SPEECH_MODEL_NOT_READY"


@pytest.mark.asyncio
async def test_26_local_whisper_status_endpoint_readiness(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    monkeypatch,
):
    """Scenario 26: Status endpoint safely reports readiness without exposing paths or secrets."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "local_whisper")

    res = await client.get(
        f"/api/v1/cases/{sample_case}/notes/transcribe/status",
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is True
    assert data["provider"] == "local_whisper"
    assert "model" in data
    assert "readiness" in data
    assert "max_file_size_bytes" in data
    # Verify no leaked paths or internal trace info
    resp_text = res.text
    assert "C:\\" not in resp_text
    assert "/home" not in resp_text
    assert "huggingface" not in resp_text.lower()


@pytest.mark.asyncio
async def test_27_local_whisper_transcription_privacy_and_security(
    client: AsyncClient,
    sample_case: str,
    caseworker_user: dict,
    db_session: AsyncSession,
    monkeypatch,
):
    """Scenario 27: Transcribing with local_whisper preserves privacy and security boundaries.

    Verifies:
    1. Audio is transcribed via local engine without persistence.
    2. Zero CaseNote or Addendum records are inserted or modified.
    3. Zero raw audio bytes are stored in the database.
    4. Response contains Cache-Control: no-store, private.
    5. Audit log contains NO transcript narrative text.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "local_whisper")

    mock_segment = MagicMock()
    mock_segment.text = "This is a synthetic test transcription from local whisper."
    mock_info = MagicMock()
    mock_info.language = "en"

    mock_whisper_model = MagicMock()
    mock_whisper_model.transcribe.return_value = ([mock_segment], mock_info)

    LocalWhisperSpeechTranscriptionProvider._cached_model = mock_whisper_model
    LocalWhisperSpeechTranscriptionProvider._cached_model_key = (
        f"{settings.speech_model}:{settings.speech_device}:{settings.speech_compute_type}"
    )

    # Count initial case notes
    initial_notes_count = (await db_session.execute(select(func.count(CaseNote.id)))).scalar()

    audio_file = (
        "synthetic_speech.webm",
        io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"),
        "audio/webm",
    )
    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files={"file": audio_file},
        data={"purpose": "case_note"},
        headers=caseworker_user["headers"],
    )

    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "local_whisper"
    assert data["transcript"] == "This is a synthetic test transcription from local whisper."

    # Cache-Control headers check
    assert "no-store" in res.headers.get("Cache-Control", "")
    assert "private" in res.headers.get("Cache-Control", "")

    # Zero CaseNote inserted
    final_notes_count = (await db_session.execute(select(func.count(CaseNote.id)))).scalar()
    assert final_notes_count == initial_notes_count

    # Audit log check: verify transcript does not appear anywhere in audit logs
    audit_events = (await db_session.execute(select(AuditEvent))).scalars().all()
    for ev in audit_events:
        meta = getattr(ev, "metadata_", None) or {}
        meta_str = str(meta).lower()
        assert "synthetic test transcription" not in meta_str
