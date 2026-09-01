"""Expanded Automated Test Suite for Phase 15 Mobile Sync Engine, Device Registration, Revocation & Tombstones."""

import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models.case import Case
from app.models.case_management import CaseRestriction
from app.models.case_note import CaseNote
from app.models.device import MobileDevice
from app.permissions.constants import Permissions
from app.services.integrations.utils import db_query_first
from app.services.sync_service import (
    get_sync_pull_delta,
    process_sync_push,
    register_mobile_device,
    revoke_mobile_device,
    validate_device_status,
)


@pytest.mark.asyncio
async def test_device_registration_and_status(db_session):
    """Verify mobile device registration and last_seen timestamp updates."""
    user_id = uuid.uuid4()
    device_id = f"DEV-{uuid.uuid4()}"

    device = await register_mobile_device(
        db=db_session,
        user_id=user_id,
        device_id=device_id,
        device_name="Pixel 8 Field Unit",
        os_type="Android",
    )
    assert device.device_id == device_id
    assert device.device_status == "ACTIVE"

    # Validate device status succeeds
    await validate_device_status(db_session, user_id, device_id)


@pytest.mark.asyncio
async def test_device_revocation_blocks_access(db_session):
    """Verify revoked device raises HTTP 403 DEVICE_REVOKED."""
    user_id = uuid.uuid4()
    device_id = f"DEV-REVOKE-{uuid.uuid4()}"

    await register_mobile_device(db_session, user_id, device_id)
    await revoke_mobile_device(db_session, device_id)

    dev = await db_query_first(db_session, MobileDevice, MobileDevice.device_id == device_id)
    assert dev.device_status == "REVOKED"

    # Validation must raise HTTP 403
    with pytest.raises(HTTPException) as exc_info:
        await validate_device_status(db_session, user_id, device_id)
    assert exc_info.value.status_code == 403
    assert "DEVICE_REVOKED" in exc_info.value.detail


@pytest.mark.asyncio
async def test_sync_pull_delta_generation(db_session):
    """Verify delta pull returns assigned authorized cases changed since timestamp."""
    user_id = uuid.uuid4()
    c1 = Case(case_number="CASE-SYNC-001", title="Authorized Sync Case", status="Active")
    db_session.add(c1)
    await db_session.commit()

    caseworker_perms = {Permissions.CASE_READ, Permissions.CASE_NOTE_READ}
    delta = await get_sync_pull_delta(db_session, user_id, caseworker_perms, last_synced_at=None)

    assert "server_timestamp" in delta
    assert any(item["case_number"] == "CASE-SYNC-001" for item in delta["cases"])


@pytest.mark.asyncio
async def test_sync_pull_tombstones_for_revoked_cases(db_session):
    """Verify delta pull returns tombstones for previously cached cases that are now restricted."""
    user_id = uuid.uuid4()
    c1 = Case(case_number="CASE-TOMB-101", title="Restricted Case 101", status="Active")
    db_session.add(c1)
    await db_session.commit()

    # Restrict user
    restriction = CaseRestriction(
        case_id=c1.id,
        user_id=user_id,
        restriction_type="conflict_of_interest",
        reason="Conflict of interest",
        is_active=True,
    )
    db_session.add(restriction)
    await db_session.commit()

    caseworker_perms = {Permissions.CASE_READ, Permissions.CASE_NOTE_READ}
    delta = await get_sync_pull_delta(
        db_session,
        user_id=user_id,
        user_permissions=caseworker_perms,
        previously_cached_case_ids=[str(c1.id)],
    )

    assert len(delta["tombstones"]) == 1
    assert delta["tombstones"][0]["entity_id"] == str(c1.id)
    assert delta["tombstones"][0]["reason"] == "RESTRICTED_OR_UNASSIGNED"


@pytest.mark.asyncio
async def test_sync_push_offline_queue_batch(db_session):
    """Verify offline case note mutation push inserts server case note record."""
    user_id = uuid.uuid4()
    c = Case(case_number="CASE-PUSH-002", title="Push Case", status="Active")
    db_session.add(c)
    await db_session.commit()

    mutation_id = str(uuid.uuid4())
    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CASE_NOTE",
            "payload": {
                "case_id": str(c.id),
                "title": "Offline Community Visit Note",
                "summary": "Met family at local health clinic in La Ronge.",
                "note_type": "Progress Note",
            },
        }
    ]

    caseworker_perms = {Permissions.CASE_READ, Permissions.CASE_NOTE_CREATE}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["status"] == "BATCH_PROCESSED"
    assert res["processed_count"] == 1
    assert res["items"][0]["status"] == "SUCCESS"

    server_id = res["items"][0]["server_id"]
    note = await db_query_first(db_session, CaseNote, CaseNote.id == uuid.UUID(server_id))
    assert note is not None
    assert note.subject == "Offline Community Visit Note"


@pytest.mark.asyncio
async def test_sync_push_idempotency(db_session):
    """Verify duplicate mutation push returns ALREADY_PROCESSED without duplicating notes."""
    user_id = uuid.uuid4()
    c = Case(case_number="CASE-IDEMP-003", title="Idempotency Case", status="Active")
    db_session.add(c)
    await db_session.commit()

    mutation_id = str(uuid.uuid4())
    item = {
        "client_mutation_id": mutation_id,
        "entity_type": "CASE_NOTE",
        "payload": {
            "case_id": str(c.id),
            "title": "Idempotent Note",
            "summary": "First upload attempt",
        },
    }

    caseworker_perms = {Permissions.CASE_READ, Permissions.CASE_NOTE_CREATE}

    # First push
    res1 = await process_sync_push(db_session, user_id, caseworker_perms, [item])
    assert res1["items"][0]["status"] == "SUCCESS"

    # Second push with identical mutation_id
    res2 = await process_sync_push(db_session, user_id, caseworker_perms, [item])
    assert res2["items"][0]["status"] == "ALREADY_PROCESSED"


@pytest.mark.asyncio
async def test_sync_push_forbidden_scope(db_session):
    """Verify offline push rejected if caseworker is restricted from target case."""
    user_id = uuid.uuid4()
    c = Case(case_number="CASE-RESTRICT-004", title="Restricted Case", status="Active")
    db_session.add(c)
    await db_session.commit()

    # Restrict user
    restriction = CaseRestriction(
        case_id=c.id,
        user_id=user_id,
        restriction_type="conflict_of_interest",
        reason="Conflict of interest",
        is_active=True,
    )
    db_session.add(restriction)
    await db_session.commit()

    item = {
        "client_mutation_id": str(uuid.uuid4()),
        "entity_type": "CASE_NOTE",
        "payload": {"case_id": str(c.id), "title": "Unauthorized Note"},
    }

    caseworker_perms = {Permissions.CASE_READ, Permissions.CASE_NOTE_CREATE}
    res = await process_sync_push(db_session, user_id, caseworker_perms, [item])
    assert res["items"][0]["status"] == "FORBIDDEN_SCOPE"


@pytest.mark.asyncio
async def test_sync_it_admin_privacy_boundary(db_session):
    """Verify IT Admin pulling sync delta receives zero cases or notes."""
    user_id = uuid.uuid4()
    c = Case(case_number="CASE-ADMIN-SYNC", title="Private Case", status="Active")
    db_session.add(c)
    await db_session.commit()

    it_admin_perms = {Permissions.ADMIN_USERS_MANAGE, Permissions.ADMIN_CONFIGURATION_MANAGE}
    delta = await get_sync_pull_delta(db_session, user_id, it_admin_perms)

    assert len(delta["cases"]) == 0
    assert len(delta["notes"]) == 0
