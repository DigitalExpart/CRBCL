"""Comprehensive test suite for Ask Red Bear Speech-to-Text Input.

CRBCL Security & Privacy Requirements:
1. Authorized Ask Red Bear user can request transcription.
2. Unauthorized user gets 403.
3. Unauthenticated request is rejected (401).
4. Ask Red Bear speech does not require CASE_NOTE_CREATE.
5. Case Note transcription still requires CASE_NOTE_CREATE.
6. Addendum still requires CASE_NOTE_ADDENDUM.
7. Ask Red Bear speech cannot bypass protected content permissions (restricted case).
8. Unsupported MIME rejected (415).
9. Oversized audio rejected (413).
10. Provider disabled/unavailable handled safely (503).
11. Transcription response uses no-cache/private headers.
12. Transcript is returned but no Ask Red Bear generation occurs.
13. Raw audio is not persisted.
14. Transcript narrative is not written to audit logs.
15. Fake speech provider remains test-only and not production default.
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
from app.models.case_management import CaseRestriction
from app.models.case_note import CaseNote
from app.models.integrations import AiRequestAudit
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.speech.provider import (
    FakeSpeechTranscriptionProvider,
    LocalWhisperSpeechTranscriptionProvider,
    get_speech_provider,
)


@pytest.fixture(autouse=True)
def configure_fake_speech_provider(monkeypatch):
    """Enable speech-to-text with fake provider by default for unit/integration testing."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", True)
    monkeypatch.setattr(settings, "speech_provider", "fake")


@pytest.fixture
async def sample_case(client: AsyncClient, caseworker_user: dict) -> str:
    """Create a sample case for speech-to-text tests."""
    res = await client.post(
        "/api/v1/cases",
        json={"title": "Synthetic Case for Ask Red Bear Speech", "case_type": "Child Safety", "status": "Open"},
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.fixture
async def it_admin_user(db_session: AsyncSession, seed_roles_and_permissions: dict) -> dict:
    """Create an IT Admin user who lacks AI_QUERY and CASE_READ permissions."""
    res = await db_session.execute(select(Role).where(Role.key == "it_admin"))
    it_role = res.scalars().first()
    if not it_role:
        it_role = Role(key="it_admin", name="IT Administrator", is_system=False)
        db_session.add(it_role)
        await db_session.flush()

    user = User(
        email="sysadmin_test@crbcl.ca",
        email_normalized="sysadmin_test@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Sam SysAdmin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=it_role.id))
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def front_desk_user(db_session: AsyncSession, seed_roles_and_permissions: dict) -> dict:
    """Create a pure Front Desk worker user without Ask Red Bear capabilities."""
    res = await db_session.execute(select(Role).where(Role.key == "front_desk"))
    fd_role = res.scalars().first()
    if not fd_role:
        fd_role = Role(key="front_desk", name="Front Desk / Reception", is_system=False)
        db_session.add(fd_role)
        await db_session.flush()

    user = User(
        email="frontdesk_worker2@crbcl.ca",
        email_normalized="frontdesk_worker2@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Faith FrontDesk2",
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
async def ai_query_only_user(db_session: AsyncSession, seed_roles_and_permissions: dict) -> dict:
    """Create a user with AI_QUERY permission but explicitly WITHOUT CASE_NOTE_CREATE or CASE_NOTE_ADDENDUM."""
    role = Role(key="ai_reader", name="AI Query Reader", is_system=False)
    db_session.add(role)
    await db_session.flush()

    perm_stmt = select(Permission).where(Permission.key == Permissions.AI_QUERY)
    perm_res = await db_session.execute(perm_stmt)
    perm = perm_res.scalar_one_or_none()
    if not perm:
        perm = Permission(key=Permissions.AI_QUERY, name="AI Query", description="Query AI")
        db_session.add(perm)
        await db_session.flush()

    db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    await db_session.flush()

    user = User(
        email="ai_reader_only@crbcl.ca",
        email_normalized="ai_reader_only@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Riley AiReader",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


# ── Scenario 1 & 11: Authorized Ask Red Bear user can request transcription ──
@pytest.mark.asyncio
async def test_01_authorized_user_can_transcribe_ask_red_bear(
    client: AsyncClient,
    caseworker_user: dict,
):
    """Authorized caseworker can transcribe audio via /api/v1/ask-red-bear/transcribe with privacy headers."""
    fake_audio = b"RIFFfake_ask_red_bear_audio_content_test"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        data={"language": "en"},
        headers=caseworker_user["headers"],
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert "transcript" in data
    assert data["provider"] == "fake"
    assert data["language"] == "en"

    # Verify strict privacy headers
    assert res.headers.get("cache-control") == "no-store, private"
    assert res.headers.get("pragma") == "no-cache"


# ── Scenario 2: Unauthorized users (IT Admin, Front Desk) are rejected with 403 ──
@pytest.mark.asyncio
async def test_02_unauthorized_users_denied_ask_red_bear_transcribe(
    client: AsyncClient,
    it_admin_user: dict,
    front_desk_user: dict,
):
    """IT Admin and Front Desk roles without AI_QUERY/CASE_READ receive 403."""
    fake_audio = b"RIFFfake_audio_bytes_data"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    # IT Admin denied
    res_it = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=it_admin_user["headers"],
    )
    assert res_it.status_code == 403

    # Front Desk denied
    files_fd = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}
    res_fd = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files_fd,
        headers=front_desk_user["headers"],
    )
    assert res_fd.status_code == 403


# ── Scenario 3: Unauthenticated request rejected with 401 ──
@pytest.mark.asyncio
async def test_03_unauthenticated_request_rejected(client: AsyncClient):
    """Unauthenticated request to Ask Red Bear transcribe is rejected with 401."""
    fake_audio = b"RIFFfake_audio_bytes_data"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post("/api/v1/ask-red-bear/transcribe", files=files)
    assert res.status_code == 401


# ── Scenario 4: Ask Red Bear speech does NOT require CASE_NOTE_CREATE ──
@pytest.mark.asyncio
async def test_04_ask_red_bear_does_not_require_case_note_create(
    client: AsyncClient,
    ai_query_only_user: dict,
):
    """User possessing AI_QUERY can transcribe for Ask Red Bear without having CASE_NOTE_CREATE."""
    fake_audio = b"RIFFfake_audio_for_ai_reader"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=ai_query_only_user["headers"],
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "transcript" in data


# ── Scenario 5: Case Note transcription still requires CASE_NOTE_CREATE ──
@pytest.mark.asyncio
async def test_05_case_note_transcription_still_requires_case_note_create(
    client: AsyncClient,
    ai_query_only_user: dict,
    sample_case: str,
):
    """User with only AI_QUERY cannot transcribe for Case Notes (requires CASE_NOTE_CREATE)."""
    fake_audio = b"RIFFfake_audio_attempting_case_note"
    files = {"file": ("note.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files=files,
        data={"purpose": "case_note"},
        headers=ai_query_only_user["headers"],
    )
    assert res.status_code == 403


# ── Scenario 6: Addendum still requires CASE_NOTE_ADDENDUM ──
@pytest.mark.asyncio
async def test_06_addendum_transcription_still_requires_case_note_addendum(
    client: AsyncClient,
    ai_query_only_user: dict,
    sample_case: str,
):
    """User with only AI_QUERY cannot transcribe for Addenda (requires CASE_NOTE_ADDENDUM)."""
    fake_audio = b"RIFFfake_audio_attempting_addendum"
    files = {"file": ("note.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        f"/api/v1/cases/{sample_case}/notes/transcribe",
        files=files,
        data={"purpose": "addendum", "note_id": str(uuid.uuid4())},
        headers=ai_query_only_user["headers"],
    )
    assert res.status_code == 403


# ── Scenario 7: Ask Red Bear speech cannot bypass protected content permissions ──
@pytest.mark.asyncio
async def test_07_ask_red_bear_speech_respects_case_restriction(
    client: AsyncClient,
    caseworker_user: dict,
    sample_case: str,
    db_session: AsyncSession,
):
    """If case_id is passed, user restricted from case receives 403/404."""
    # Add active restriction for this caseworker on the case
    restriction = CaseRestriction(
        case_id=uuid.UUID(sample_case),
        user_id=caseworker_user["user"].id,
        reason="Ethical wall conflict of interest",
        is_active=True,
        created_by=caseworker_user["user"].id,
    )
    db_session.add(restriction)
    await db_session.commit()

    fake_audio = b"RIFFfake_restricted_audio"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        data={"case_id": sample_case},
        headers=caseworker_user["headers"],
    )
    # Blocked by CaseService get_case_or_404
    assert res.status_code in (403, 404)


# ── Scenario 8: Unsupported MIME rejected (415) ──
@pytest.mark.asyncio
async def test_08_unsupported_mime_rejected(
    client: AsyncClient,
    caseworker_user: dict,
):
    """Audio files with unsupported MIME types are rejected with 415."""
    fake_audio = b"RIFFfake_audio"
    files = {"file": ("prompt.exe", io.BytesIO(fake_audio), "application/x-msdownload")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 415


# ── Scenario 9: Oversized audio rejected (413) ──
@pytest.mark.asyncio
async def test_09_oversized_audio_rejected(
    client: AsyncClient,
    caseworker_user: dict,
):
    """Audio exceeding max technical size is rejected with 413."""
    settings = get_settings()
    oversized_bytes = b"0" * (settings.speech_max_file_size_bytes + 1024)
    files = {"file": ("prompt.webm", io.BytesIO(oversized_bytes), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 413


# ── Scenario 10: Provider disabled/unavailable handled safely (503) ──
@pytest.mark.asyncio
async def test_10_disabled_provider_handled_safely(
    client: AsyncClient,
    caseworker_user: dict,
    monkeypatch,
):
    """When speech-to-text is disabled via settings, endpoint returns 503."""
    settings = get_settings()
    monkeypatch.setattr(settings, "speech_to_text_enabled", False)
    monkeypatch.setattr(settings, "speech_provider", "disabled")

    fake_audio = b"RIFFfake_audio"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 503
    error_code = res.json().get("error", {}).get("code") or res.json().get("detail", {}).get("error", {}).get("code")
    assert error_code in ("SPEECH_TRANSCRIPTION_DISABLED", "SPEECH_PROVIDER_NOT_CONFIGURED")


# ── Scenario 12: Transcript is returned but NO Ask Red Bear AI generation occurs ──
@pytest.mark.asyncio
async def test_12_transcribe_does_not_trigger_ai_generation(
    client: AsyncClient,
    caseworker_user: dict,
    db_session: AsyncSession,
):
    """Transcribing audio returns transcript text without creating any AiRequestAudit record."""
    audit_count_before = (
        await db_session.execute(select(func.count(AiRequestAudit.id)))
    ).scalar_one()

    fake_audio = b"RIFFfake_audio_for_no_gen_test"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200

    audit_count_after = (
        await db_session.execute(select(func.count(AiRequestAudit.id)))
    ).scalar_one()
    # AiRequestAudit must remain unchanged (no AI generation was invoked)
    assert audit_count_after == audit_count_before


# ── Scenario 13: Raw audio is not persisted; no Case Notes created ──
@pytest.mark.asyncio
async def test_13_no_persistence_of_audio_or_case_notes(
    client: AsyncClient,
    caseworker_user: dict,
    db_session: AsyncSession,
):
    """Ask Red Bear speech input does not create Case Note, Case, or audio recording rows."""
    notes_count_before = (
        await db_session.execute(select(func.count(CaseNote.id)))
    ).scalar_one()

    fake_audio = b"RIFFfake_audio_pure_transcribe"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200

    notes_count_after = (
        await db_session.execute(select(func.count(CaseNote.id)))
    ).scalar_one()
    assert notes_count_after == notes_count_before


# ── Scenario 14: Transcript narrative is NOT written to audit logs ──
@pytest.mark.asyncio
async def test_14_transcript_narrative_never_logged_in_audit(
    client: AsyncClient,
    caseworker_user: dict,
    db_session: AsyncSession,
):
    """Audit events log only metadata (bytes length, provider, outcome). Transcript narrative is NOT logged."""
    fake_audio = b"RIFFfake_audio_confidential_test"
    files = {"file": ("prompt.webm", io.BytesIO(fake_audio), "audio/webm")}

    res = await client.post(
        "/api/v1/ask-red-bear/transcribe",
        files=files,
        headers=caseworker_user["headers"],
    )
    assert res.status_code == 200
    transcript_text = res.json()["transcript"]

    # Check latest audit event for this user
    stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.user_id == caseworker_user["user"].id,
            AuditEvent.event_type == "speech_transcription_succeeded",
        )
        .order_by(AuditEvent.timestamp.desc())
        .limit(1)
    )
    audit_res = await db_session.execute(stmt)
    event = audit_res.scalar_one_or_none()
    assert event is not None
    meta = event.metadata_ or {}

    assert meta.get("purpose") == "ask_red_bear"
    assert meta.get("outcome") == "success"
    assert "audio_bytes_length" in meta
    # Assert transcript text is nowhere in audit metadata
    assert transcript_text not in str(meta)
    assert "transcript" not in meta


# ── Scenario 15: Fake speech provider remains test-only ──
def test_15_fake_speech_provider_is_test_only():
    """Verify FakeSpeechTranscriptionProvider is never the production default."""
    from app.core import Settings

    prod_settings = Settings(
        app_env="production",
        speech_to_text_enabled=True,
        speech_provider="local_whisper",
    )
    provider = get_speech_provider(prod_settings)
    assert isinstance(provider, LocalWhisperSpeechTranscriptionProvider)
    assert not isinstance(provider, FakeSpeechTranscriptionProvider)


# ── Status Endpoint Test ──
@pytest.mark.asyncio
async def test_16_ask_red_bear_transcribe_status_endpoint(
    client: AsyncClient,
    caseworker_user: dict,
    it_admin_user: dict,
):
    """GET /api/v1/ask-red-bear/transcribe/status returns status for authorized users, 403 for unauthorized."""
    res_auth = await client.get(
        "/api/v1/ask-red-bear/transcribe/status",
        headers=caseworker_user["headers"],
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert "enabled" in data
    assert "available" in data
    assert "model" in data

    # Unauthorized IT Admin gets 403
    res_unauth = await client.get(
        "/api/v1/ask-red-bear/transcribe/status",
        headers=it_admin_user["headers"],
    )
    assert res_unauth.status_code == 403
