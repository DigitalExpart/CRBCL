"""Automated Tests for Extended Mobile Synchronization (Client, Intake, Home Visit, Follow-up, RBAC, Duplicates)."""

import uuid
from datetime import date, datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.models.calendar import CalendarEvent
from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.client import Client
from app.models.device import MobileDevice
from app.models.person import Person
from app.models.referral import Referral
from app.permissions.constants import Permissions
from app.services.integrations.utils import db_query_first
from app.services.sync_service import (
    process_sync_push,
    register_mobile_device,
    validate_device_status,
)


@pytest.mark.asyncio
async def test_sync_push_client_creation_clean(db_session):
    """Verify clean offline Client mutation generates 10-digit Person ID and Client record."""
    user_id = uuid.uuid4()
    mutation_id = str(uuid.uuid4())
    temp_client_id = str(uuid.uuid4())

    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CLIENT",
            "payload": {
                "temp_id": temp_client_id,
                "first_name": "Wapusk",
                "last_name": f"Muskego_{uuid.uuid4().hex[:6]}",
                "date_of_birth": "1994-03-21",
                "gender": "Male",
                "phone": "306-555-0199",
                "email": f"wapusk_{uuid.uuid4().hex[:4]}@example.com",
                "treaty_number": f"TR-{uuid.uuid4().hex[:6]}",
                "band_nation": "Cote First Nation",
                "status": "Active",
            },
        }
    ]

    caseworker_perms = {Permissions.CLIENT_CREATE, Permissions.CASE_READ}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["status"] == "BATCH_PROCESSED"
    assert res["processed_count"] == 1
    item_res = res["items"][0]
    assert item_res["status"] == "SUCCESS"
    assert "server_id" in item_res
    assert "person_id_number" in item_res

    # Permanent Person ID must be exactly 10 digits
    person_id_num = item_res["person_id_number"]
    assert len(person_id_num) == 10
    assert person_id_num.isdigit()

    # Verify Client in DB
    client = await db_query_first(db_session, Client, Client.id == uuid.UUID(item_res["server_id"]))
    assert client is not None
    assert client.first_name == "Wapusk"
    assert client.person_id is not None

    # Verify canonical Person
    person = await db_query_first(db_session, Person, Person.id == client.person_id)
    assert person is not None
    assert person.person_id_number == person_id_num


@pytest.mark.asyncio
async def test_sync_push_client_duplicate_detection(db_session):
    """Verify offline Client mutation matching existing person >= 0.85 returns NEEDS_REVIEW."""
    user_id = uuid.uuid4()

    # Pre-create an existing person
    existing_person = Person(
        person_id_number=str(uuid.uuid4().int)[:10],
        first_name="Alexander",
        last_name="Brass",
        date_of_birth=date(1990, 5, 12),
        phone="306-555-1212",
        email="alex.brass@example.com",
        treaty_number="TR-654321",
    )
    db_session.add(existing_person)
    await db_session.commit()

    mutation_id = str(uuid.uuid4())
    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CLIENT",
            "payload": {
                "first_name": "Alexander",
                "last_name": "Brass",
                "date_of_birth": "1990-05-12",
                "phone": "306-555-1212",
                "treaty_number": "TR-654321",
            },
        }
    ]

    caseworker_perms = {Permissions.CLIENT_CREATE, Permissions.CASE_READ}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["status"] == "BATCH_PROCESSED"
    item_res = res["items"][0]
    # Must flag for review and NOT create duplicate
    assert item_res["status"] == "NEEDS_REVIEW"
    assert "candidates" in item_res
    assert len(item_res["candidates"]) > 0


@pytest.mark.asyncio
async def test_sync_push_intake_creation(db_session):
    """Verify offline Intake mutation creates Referral with sequential INT-YYYY-NNNNNN."""
    user_id = uuid.uuid4()
    mutation_id = str(uuid.uuid4())

    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "INTAKE",
            "payload": {
                "summary": "Urgent family housing and wellness referral from local health center.",
                "received_date": date.today().isoformat(),
                "priority": "High",
                "immediate_safety_concerns": False,
                "community": "Kamsack",
            },
        }
    ]

    caseworker_perms = {Permissions.INTAKE_CREATE, Permissions.CASE_READ}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["status"] == "BATCH_PROCESSED"
    item_res = res["items"][0]
    assert item_res["status"] == "SUCCESS"
    assert "referral_number" in item_res

    ref_num = item_res["referral_number"]
    assert ref_num.startswith("INT-")

    referral = await db_query_first(db_session, Referral, Referral.id == uuid.UUID(item_res["server_id"]))
    assert referral is not None
    assert referral.referral_number == ref_num
    assert referral.priority == "High"


@pytest.mark.asyncio
async def test_sync_push_home_visit_and_followup(db_session):
    """Verify offline Home Visit and Follow-up mutations create CalendarEvent rows."""
    user_id = uuid.uuid4()
    case = Case(case_number="CASE-CAL-100", title="Calendar Case", status="Active")
    db_session.add(case)
    await db_session.commit()

    mut_hv = str(uuid.uuid4())
    mut_fu = str(uuid.uuid4())

    push_items = [
        {
            "client_mutation_id": mut_hv,
            "entity_type": "HOME_VISIT",
            "payload": {
                "case_id": str(case.id),
                "title": "Family Wellness Check",
                "notes": "Conducted in-person check-in at family residence.",
                "location": "Cote First Nation, House 42",
            },
        },
        {
            "client_mutation_id": mut_fu,
            "entity_type": "FOLLOW_UP",
            "payload": {
                "case_id": str(case.id),
                "title": "Follow up with school counselor",
                "notes": "Verify attendance records and after-school support program.",
            },
        },
    ]

    caseworker_perms = {Permissions.CASE_READ, Permissions.APPOINTMENT_MANAGE}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["status"] == "BATCH_PROCESSED"
    assert res["items"][0]["status"] == "SUCCESS"
    assert res["items"][1]["status"] == "SUCCESS"

    hv_event = await db_query_first(db_session, CalendarEvent, CalendarEvent.id == uuid.UUID(res["items"][0]["server_id"]))
    assert hv_event is not None
    assert hv_event.event_type == "HOME_VISIT"
    assert hv_event.location == "Cote First Nation, House 42"

    fu_event = await db_query_first(db_session, CalendarEvent, CalendarEvent.id == uuid.UUID(res["items"][1]["server_id"]))
    assert fu_event is not None
    assert fu_event.event_type == "CASE_NOTE_FOLLOWUP"


@pytest.mark.asyncio
async def test_sync_push_permission_denial(db_session):
    """Verify caseworker without client.create cannot push Client registration."""
    user_id = uuid.uuid4()
    mutation_id = str(uuid.uuid4())

    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CLIENT",
            "payload": {
                "first_name": "Test",
                "last_name": "Unauthorized",
            },
        }
    ]

    # Only case read permission, NO client.create
    limited_perms = {Permissions.CASE_READ}
    res = await process_sync_push(db_session, user_id, limited_perms, push_items)

    assert res["status"] == "BATCH_PROCESSED"
    assert res["items"][0]["status"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_sync_push_idempotent_retry_returns_authoritative_ids(db_session):
    """Verify repeated push of already-processed client mutation returns authoritative permanent IDs."""
    user_id = uuid.uuid4()
    mutation_id = str(uuid.uuid4())
    temp_client_id = str(uuid.uuid4())

    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CLIENT",
            "payload": {
                "temp_id": temp_client_id,
                "first_name": "Tatanka",
                "last_name": f"Awasis_{uuid.uuid4().hex[:6]}",
                "date_of_birth": "1998-07-14",
                "status": "Active",
            },
        }
    ]

    caseworker_perms = {Permissions.CLIENT_CREATE, Permissions.CASE_READ}
    # Initial push
    first_res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)
    assert first_res["items"][0]["status"] == "SUCCESS"
    first_server_id = first_res["items"][0]["server_id"]
    first_person_id_num = first_res["items"][0]["person_id_number"]

    # Retried push (e.g. lost response or repeated sync)
    second_res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)
    assert second_res["items"][0]["status"] == "ALREADY_PROCESSED"
    assert second_res["items"][0]["server_id"] == first_server_id
    assert second_res["items"][0]["person_id_number"] == first_person_id_num


@pytest.mark.asyncio
async def test_sync_duplicate_candidate_privacy_sanitization(db_session):
    """Verify candidate payloads in NEEDS_REVIEW never leak raw treaty or health card numbers."""
    user_id = uuid.uuid4()

    # Pre-create candidate with sensitive statutory identifier
    existing_person = Person(
        person_id_number=str(uuid.uuid4().int)[:10],
        first_name="Kiyana",
        last_name="Cardinal",
        date_of_birth=date(1995, 2, 10),
        treaty_number="TR-PRIVATE-9999",
        health_card_number="SK-HEALTH-8888",
    )
    db_session.add(existing_person)
    await db_session.commit()

    mutation_id = str(uuid.uuid4())
    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CLIENT",
            "payload": {
                "first_name": "Kiyana",
                "last_name": "Cardinal",
                "date_of_birth": "1995-02-10",
                "treaty_number": "TR-PRIVATE-9999",
            },
        }
    ]

    caseworker_perms = {Permissions.CLIENT_CREATE, Permissions.CASE_READ}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["items"][0]["status"] == "NEEDS_REVIEW"
    candidates = res["items"][0]["candidates"]
    assert len(candidates) > 0
    for cand in candidates:
        assert "treaty_number" not in cand
        assert "health_card_number" not in cand
        assert cand["first_name"] == "Kiyana"
        assert cand["last_name"] == "Cardinal"


@pytest.mark.asyncio
async def test_sync_device_user_mismatch_rejected(db_session):
    """Verify mobile synchronization rejects requests when device is registered to another user."""
    owner_user_id = uuid.uuid4()
    attacker_user_id = uuid.uuid4()
    device_id = f"DEV-{uuid.uuid4().hex[:12]}"

    # Register device for owner
    await register_mobile_device(db_session, owner_user_id, device_id)

    # Attacker tries to validate or sync with owner's device_id
    with pytest.raises(HTTPException) as exc_info:
        await validate_device_status(db_session, attacker_user_id, device_id)

    assert exc_info.value.status_code == 403
    assert "DEVICE_USER_MISMATCH" in exc_info.value.detail


@pytest.mark.asyncio
async def test_sync_case_note_draft_and_safety(db_session):
    """Verify offline case notes sync as DRAFT, is_locked=False, and enforce valid case_id."""
    user_id = uuid.uuid4()
    case = Case(case_number="CASE-NOTE-TEST-01", title="Safety Case", status="Active")
    db_session.add(case)
    await db_session.commit()

    mut_valid = str(uuid.uuid4())
    mut_invalid_case = str(uuid.uuid4())

    push_items = [
        {
            "client_mutation_id": mut_valid,
            "entity_type": "CASE_NOTE",
            "payload": {
                "case_id": str(case.id),
                "title": "Field Visit Notes",
                "summary": "Observations from home assessment.",
            },
        },
        {
            "client_mutation_id": mut_invalid_case,
            "entity_type": "CASE_NOTE",
            "payload": {
                "title": "Missing Case Note",
                "summary": "Note without a target case.",
            },
        },
    ]

    caseworker_perms = {Permissions.CASE_READ, Permissions.CASE_NOTE_CREATE}
    res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["items"][0]["status"] == "SUCCESS"
    assert res["items"][1]["status"] == "FAILED"

    note = await db_query_first(db_session, CaseNote, CaseNote.id == uuid.UUID(res["items"][0]["server_id"]))
    assert note is not None
    assert note.status == "DRAFT"
    assert note.is_locked is False
    assert note.locked_at is None
    assert note.locked_by is None


@pytest.mark.asyncio
async def test_sync_push_partial_failure_savepoint_rollback(db_session):
    """Verify that failure during Client creation rolls back Person via transaction savepoint."""
    user_id = uuid.uuid4()
    mutation_id = str(uuid.uuid4())
    unique_last = f"RollbackTest_{uuid.uuid4().hex[:8]}"

    push_items = [
        {
            "client_mutation_id": mutation_id,
            "entity_type": "CLIENT",
            "payload": {
                "first_name": "TestPerson",
                "last_name": unique_last,
                "date_of_birth": "2001-01-01",
            },
        }
    ]

    caseworker_perms = {Permissions.CLIENT_CREATE, Permissions.CASE_READ}

    # Simulate failure during Client instantiation/persistence inside the item savepoint
    with patch("app.services.sync_service.Client", side_effect=RuntimeError("Simulated client database error")):
        res = await process_sync_push(db_session, user_id, caseworker_perms, push_items)

    assert res["items"][0]["status"] == "FAILED"
    assert "Simulated client database error" in res["items"][0]["error"]

    # Verify no partial Person record was left behind
    orphan_person = await db_query_first(db_session, Person, Person.last_name == unique_last)
    assert orphan_person is None


@pytest.mark.asyncio
async def test_sync_config_feature_flag_status(client, caseworker_user, supervisor_user):
    """Verify /api/v1/sync/config returns feature flag and user eligibility correctly."""
    # 1. Caseworker with feature flag OFF (default)
    res_cw = await client.get("/api/v1/sync/config", headers=caseworker_user["headers"])
    assert res_cw.status_code == 200
    data_cw = res_cw.json()
    assert data_cw["offline_web_enabled"] is False
    assert data_cw["user_eligible"] is False
    assert "server_time" in data_cw

    # 2. Supervisor with feature flag OFF (eligible for controlled testing)
    res_sup = await client.get("/api/v1/sync/config", headers=supervisor_user["headers"])
    assert res_sup.status_code == 200
    data_sup = res_sup.json()
    assert data_sup["offline_web_enabled"] is False
    assert data_sup["user_eligible"] is True

    # 3. When feature flag is ON, all users become eligible
    with patch("app.core.get_settings") as mock_settings:
        mock_settings.return_value.crbcl_offline_web_enabled = True
        res_enabled = await client.get("/api/v1/sync/config", headers=caseworker_user["headers"])
        assert res_enabled.status_code == 200
        data_enabled = res_enabled.json()
        assert data_enabled["offline_web_enabled"] is True
        assert data_enabled["user_eligible"] is True


@pytest.mark.asyncio
async def test_sync_push_web_client_feature_flag_enforcement(client, caseworker_user, supervisor_user):
    """Verify web client push enforces feature flag and rejects non-admin users when flag is false."""
    mutation_id = str(uuid.uuid4())
    push_payload = {
        "items": [
            {
                "client_mutation_id": mutation_id,
                "entity_type": "CLIENT",
                "payload": {
                    "first_name": "Offline",
                    "last_name": "WebUser",
                    "date_of_birth": "1990-01-01",
                },
            }
        ]
    }

    # 1. Caseworker pushing via web client when flag is OFF -> HTTP 403 OFFLINE_WEB_DISABLED
    headers_web_cw = {**caseworker_user["headers"], "X-Client-Type": "web", "X-Device-ID": "WEB-BROWSER-TEST-01"}
    res_blocked = await client.post("/api/v1/sync/push", json=push_payload, headers=headers_web_cw)
    assert res_blocked.status_code == 403
    err_body = res_blocked.json()
    assert "OFFLINE_WEB_DISABLED" in (err_body.get("detail") or err_body.get("error", {}).get("message", ""))

    # 2. Supervisor pushing via web client when flag is OFF -> Allowed (test account exemption)
    headers_web_sup = {**supervisor_user["headers"], "X-Client-Type": "web", "X-Device-ID": "WEB-BROWSER-TEST-02"}
    res_allowed = await client.post("/api/v1/sync/push", json=push_payload, headers=headers_web_sup)
    assert res_allowed.status_code == 200
    assert res_allowed.json()["status"] == "BATCH_PROCESSED"

    # 3. Caseworker pushing via web client when flag is ON -> Allowed
    with patch("app.core.get_settings") as mock_settings:
        mock_settings.return_value.crbcl_offline_web_enabled = True
        mutation_id_2 = str(uuid.uuid4())
        push_payload_2 = {
            "items": [
                {
                    "client_mutation_id": mutation_id_2,
                    "entity_type": "CLIENT",
                    "payload": {
                        "first_name": "OfflineEnabled",
                        "last_name": "WebUser2",
                        "date_of_birth": "1992-02-02",
                    },
                }
            ]
        }
        res_enabled = await client.post("/api/v1/sync/push", json=push_payload_2, headers=headers_web_cw)
        assert res_enabled.status_code == 200
        assert res_enabled.json()["status"] == "BATCH_PROCESSED"
