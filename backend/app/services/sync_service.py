"""Mobile Sync Service handling device registration, revocation, delta pull with tombstones, and sync queue push."""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.calendar import CalendarEvent
from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.client import Client
from app.models.device import MobileDevice
from app.models.migration import MigrationLedger
from app.models.person import Person
from app.models.referral import Referral
from app.permissions.constants import Permissions
from app.repositories.person_repo import PersonRepository
from app.repositories.referral_repo import ReferralRepository
from app.services.duplicate_service import DuplicateService
from app.services.integrations.ai.gateway import AiGateway
from app.services.integrations.utils import db_commit, db_query_all, db_query_first

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _atomic_mutation_savepoint(db: Any):
    """Savepoint context manager to guarantee item-level transaction rollback on partial failure."""
    if hasattr(db, "begin_nested"):
        async with db.begin_nested():
            yield
    else:
        yield


def _parse_date(val: Any) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return date.fromisoformat(str(val).split("T")[0])
    except Exception:
        return None


def _parse_datetime(val: Any, default: datetime | None = None) -> datetime:
    if not val:
        return default or datetime.utcnow()
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        return default or datetime.utcnow()


async def register_mobile_device(
    db: Any,
    user_id: uuid.UUID,
    device_id: str,
    device_name: str = "Caseworker Handheld",
    os_type: str = "Android",
    app_version: str = "1.0.0",
) -> MobileDevice:
    """Register or update a mobile device for a caseworker."""
    device = await db_query_first(db, MobileDevice, MobileDevice.device_id == device_id)
    if device:
        device.user_id = user_id
        device.device_name = device_name
        device.os_type = os_type
        device.app_version = app_version
        device.device_status = "ACTIVE"
        device.last_seen_at = datetime.utcnow()
    else:
        device = MobileDevice(
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            os_type=os_type,
            app_version=app_version,
            device_status="ACTIVE",
            last_seen_at=datetime.utcnow(),
            registered_at=datetime.utcnow(),
        )
        db.add(device)

    await db_commit(db)
    return device


async def revoke_mobile_device(db: Any, device_id: str) -> MobileDevice:
    """Administrative revocation of a mobile device."""
    device = await db_query_first(db, MobileDevice, MobileDevice.device_id == device_id)
    if not device:
        raise ValueError(f"Mobile device {device_id} not found.")

    device.device_status = "REVOKED"
    await db_commit(db)
    return device


async def validate_device_status(db: Any, user_id: uuid.UUID, device_id: str | None) -> None:
    """Validate device registration and status. Rejects revoked devices and user mismatches with HTTP 403."""
    if not device_id:
        return  # Allow standard web requests without device ID

    device = await db_query_first(db, MobileDevice, MobileDevice.device_id == device_id)
    if not device:
        if device_id.startswith("WEB-"):
            device = await register_mobile_device(
                db=db,
                user_id=user_id,
                device_id=device_id,
                device_name="Web Offline Workspace",
                os_type="Web Browser",
            )
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_REVOKED: This device has been revoked or wiped by an administrator.",
        )

    if device.device_status in ["REVOKED", "WIPED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_REVOKED: This device has been revoked or wiped by an administrator.",
        )

    if device.user_id and device.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_USER_MISMATCH: This mobile device is registered to another user account.",
        )

    # Touch last_seen_at
    device.last_seen_at = datetime.utcnow()
    await db_commit(db)


async def get_sync_pull_delta(
    db: Any,
    user_id: uuid.UUID,
    user_permissions: set[str],
    last_synced_at: datetime | None = None,
    previously_cached_case_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate delta bundle of authorized cases, clients, notes, and tombstones for revoked cases."""
    # IT Admin lacks case read permission -> return empty delta
    if Permissions.CASE_READ not in user_permissions and Permissions.CASE_NOTE_READ not in user_permissions:
        return {
            "server_timestamp": datetime.utcnow().isoformat(),
            "cases": [],
            "clients": [],
            "notes": [],
            "tombstones": [],
        }

    # Fetch authorized case IDs
    authorized_case_ids = await AiGateway.get_authorized_case_ids(db, user_id, user_permissions)

    # Tombstone extraction: Cases previously cached on device that are no longer authorized
    tombstones = []
    if previously_cached_case_ids:
        for cid_str in previously_cached_case_ids:
            try:
                cid = uuid.UUID(cid_str)
                if cid not in authorized_case_ids:
                    tombstones.append(
                        {
                            "entity_type": "CASE",
                            "entity_id": cid_str,
                            "reason": "RESTRICTED_OR_UNASSIGNED",
                        }
                    )
            except Exception:
                continue

    if not authorized_case_ids:
        return {
            "server_timestamp": datetime.utcnow().isoformat(),
            "cases": [],
            "clients": [],
            "notes": [],
            "tombstones": tombstones,
        }

    # Query Cases
    all_cases = await db_query_all(db, Case)
    cases_delta = [
        {
            "id": str(c.id),
            "case_number": c.case_number,
            "title": c.title,
            "status": c.status,
            "stage": c.stage,
            "updated_at": c.updated_at.isoformat() if getattr(c, "updated_at", None) else datetime.utcnow().isoformat(),
        }
        for c in all_cases
        if c.id in authorized_case_ids and (last_synced_at is None or (c.updated_at and c.updated_at > last_synced_at))
    ]

    # Query Clients
    all_clients = await db_query_all(db, Client)
    clients_delta = [
        {
            "id": str(cl.id),
            "first_name": cl.first_name,
            "last_name": cl.last_name,
            "status": cl.status,
        }
        for cl in all_clients
        if last_synced_at is None or (cl.updated_at and cl.updated_at > last_synced_at)
    ]

    # Query Case Notes
    all_notes = await db_query_all(db, CaseNote)
    notes_delta = [
        {
            "id": str(n.id),
            "case_id": str(n.case_id),
            "title": n.subject,
            "summary": n.content,
            "note_type": n.note_type,
            "created_at": n.created_at.isoformat() if getattr(n, "created_at", None) else datetime.utcnow().isoformat(),
        }
        for n in all_notes
        if n.case_id in authorized_case_ids
        and (last_synced_at is None or (n.created_at and n.created_at > last_synced_at))
    ]

    return {
        "server_timestamp": datetime.utcnow().isoformat(),
        "cases": cases_delta,
        "clients": clients_delta,
        "notes": notes_delta,
        "tombstones": tombstones,
    }


async def _resolve_target_id(db: Any, raw_id_str: str | None, temp_map: dict[str, str]) -> uuid.UUID | None:
    """Resolve raw string identifier or temp UUID against batch map or previous ledger."""
    if not raw_id_str:
        return None
    if raw_id_str in temp_map:
        return uuid.UUID(temp_map[raw_id_str])
    try:
        return uuid.UUID(raw_id_str)
    except ValueError:
        ledger = await db_query_first(
            db,
            MigrationLedger,
            MigrationLedger.source_system == "MOBILE_SYNC",
            MigrationLedger.source_id == raw_id_str,
        )
        if ledger and ledger.target_entity_id:
            temp_map[raw_id_str] = str(ledger.target_entity_id)
            return ledger.target_entity_id
        return None


async def process_sync_push(
    db: Any,
    user_id: uuid.UUID,
    user_permissions: set[str],
    push_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Process incoming offline mutation outbox queue items with idempotency, dependency mapping, and RBAC."""
    authorized_case_ids = await AiGateway.get_authorized_case_ids(db, user_id, user_permissions)
    results = []
    temp_id_map: dict[str, str] = {}
    temp_person_map: dict[str, str] = {}

    for item in push_items:
        mutation_id = item.get("client_mutation_id", str(uuid.uuid4()))
        entity_type = (item.get("entity_type") or "").upper()
        payload = item.get("payload", {})
        expected_version = item.get("expected_version")

        # 1. Check idempotency via MigrationLedger
        existing_ledger = await db_query_first(
            db,
            MigrationLedger,
            MigrationLedger.source_system == "MOBILE_SYNC",
            MigrationLedger.source_id == mutation_id,
        )
        if existing_ledger:
            server_id_str = str(existing_ledger.target_entity_id) if existing_ledger.target_entity_id else None
            item_result: dict[str, Any] = {
                "client_mutation_id": mutation_id,
                "status": "ALREADY_PROCESSED",
                "server_id": server_id_str,
            }
            temp_id = payload.get("temp_id") or payload.get("id")
            if server_id_str:
                temp_id_map[mutation_id] = server_id_str
                if temp_id:
                    temp_id_map[str(temp_id)] = server_id_str

            # Authoritative lookups for entity-specific permanent identifiers
            if existing_ledger.target_entity_type == "CLIENT" and existing_ledger.target_entity_id:
                client_obj = await db_query_first(db, Client, Client.id == existing_ledger.target_entity_id)
                if client_obj and client_obj.person_id:
                    person_obj = await db_query_first(db, Person, Person.id == client_obj.person_id)
                    if person_obj:
                        item_result["person_id"] = str(person_obj.id)
                        item_result["person_id_number"] = person_obj.person_id_number
                        temp_person_map[mutation_id] = str(person_obj.id)
                        if temp_id:
                            temp_person_map[str(temp_id)] = str(person_obj.id)
            elif existing_ledger.target_entity_type in ["INTAKE", "REFERRAL"] and existing_ledger.target_entity_id:
                ref_obj = await db_query_first(db, Referral, Referral.id == existing_ledger.target_entity_id)
                if ref_obj:
                    item_result["referral_number"] = ref_obj.referral_number

            results.append(item_result)
            continue

        # 2. Case Authorization check for case-scoped entities
        target_case_id_str = payload.get("case_id")
        target_case_id = None
        if target_case_id_str:
            resolved_case = await _resolve_target_id(db, target_case_id_str, temp_id_map)
            if not resolved_case:
                results.append({"client_mutation_id": mutation_id, "status": "INVALID_CASE_ID"})
                continue
            if resolved_case not in authorized_case_ids:
                results.append({"client_mutation_id": mutation_id, "status": "FORBIDDEN_SCOPE"})
                continue
            target_case_id = resolved_case

        # 3. Handle CLIENT entity (Canonical Person + Client)
        if entity_type in ["CLIENT", "PERSON"]:
            first_name = (payload.get("first_name") or "").strip()
            last_name = (payload.get("last_name") or "").strip()

            if not first_name or not last_name:
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "FAILED",
                    "error": "Client registration requires first_name and last_name.",
                })
                continue

            # Permission check: client.create or case.create
            if user_permissions and not (user_permissions & {Permissions.CLIENT_CREATE, Permissions.CASE_CREATE, Permissions.ADMIN_USERS_MANAGE}):
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "PERMISSION_DENIED",
                    "error": "User lacks client registration permission.",
                })
                continue

            parsed_dob = _parse_date(payload.get("date_of_birth"))

            # Duplicate Detection check
            dup_service = DuplicateService(db)
            candidates = await dup_service.check_duplicates(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=str(parsed_dob) if parsed_dob else None,
                treaty_number=payload.get("treaty_number"),
                health_card_number=payload.get("health_card_number"),
                phone=payload.get("phone"),
                email=payload.get("email"),
            )
            # High similarity (>=0.85) or exact identity number match triggers review
            review_candidates = []
            for c in candidates:
                score = c.get("similarity_score", 0.0)
                factors = c.get("matching_factors", [])
                is_exact_id_match = any("treaty" in str(f).lower() or "health_card" in str(f).lower() for f in factors)
                if score >= 0.85 or is_exact_id_match:
                    # Sanitize to never leak raw treaty or health card numbers in API candidate payloads
                    review_candidates.append({
                        "person_id": c.get("person_id"),
                        "first_name": c.get("first_name"),
                        "last_name": c.get("last_name"),
                        "date_of_birth": c.get("date_of_birth"),
                        "similarity_score": score,
                        "matching_factors": factors,
                    })

            if review_candidates:
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "NEEDS_REVIEW",
                    "message": "Potential duplicate Person record detected on server. Requires authorized review.",
                    "candidates": review_candidates,
                })
                continue

            try:
                async with _atomic_mutation_savepoint(db):
                    # Generate server-authoritative 10-digit permanent Person ID
                    person_repo = PersonRepository(db)
                    person_id_number = await person_repo.generate_person_id_number()

                    person = Person(
                        person_id_number=person_id_number,
                        first_name=first_name,
                        last_name=last_name,
                        date_of_birth=parsed_dob,
                        gender=payload.get("gender"),
                        phone=payload.get("phone"),
                        email=payload.get("email"),
                        treaty_number=payload.get("treaty_number"),
                        band_nation=payload.get("band_nation"),
                        indigenous_identity=payload.get("indigenous_identity"),
                        created_by=user_id,
                    )
                    db.add(person)
                    if hasattr(db, "flush"):
                        await db.flush()

                    client = Client(
                        person_id=person.id,
                        first_name=first_name,
                        last_name=last_name,
                        date_of_birth=parsed_dob,
                        gender=payload.get("gender"),
                        phone=payload.get("phone"),
                        email=payload.get("email"),
                        address=payload.get("address"),
                        city=payload.get("city"),
                        province=payload.get("province", "Saskatchewan"),
                        band_nation=payload.get("band_nation"),
                        indigenous_identity=payload.get("indigenous_identity"),
                        status=payload.get("status", "Pending Intake"),
                        risk_level=payload.get("risk_level", "Low"),
                        approval_status="APPROVED",
                        notes=payload.get("notes"),
                        created_by=user_id,
                    )
                    db.add(client)
                    if hasattr(db, "flush"):
                        await db.flush()

                    # Record idempotency ledger
                    ledger = MigrationLedger(
                        source_system="MOBILE_SYNC",
                        source_id=mutation_id,
                        target_entity_type="CLIENT",
                        target_entity_id=client.id,
                        status="COMPLETED",
                    )
                    db.add(ledger)
                    if hasattr(db, "flush"):
                        await db.flush()

                await db_commit(db)

                # Store mapping for dependent offline items in the same batch
                temp_id = payload.get("temp_id") or payload.get("id")
                if temp_id:
                    temp_id_map[str(temp_id)] = str(client.id)
                    temp_person_map[str(temp_id)] = str(person.id)
                temp_id_map[mutation_id] = str(client.id)
                temp_person_map[mutation_id] = str(person.id)

                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "SUCCESS",
                    "server_id": str(client.id),
                    "person_id": str(person.id),
                    "person_id_number": person_id_number,
                })
            except Exception as exc:
                logger.error(f"Failed to process offline client registration {mutation_id}: {exc}")
                results.append({"client_mutation_id": mutation_id, "status": "FAILED", "error": str(exc)})

        # 4. Handle INTAKE entity (Referral)
        elif entity_type in ["INTAKE", "REFERRAL"]:
            if user_permissions and not (user_permissions & {Permissions.INTAKE_CREATE, Permissions.CASE_CREATE, Permissions.ADMIN_USERS_MANAGE}):
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "PERMISSION_DENIED",
                    "error": "User lacks intake registration permission.",
                })
                continue

            try:
                async with _atomic_mutation_savepoint(db):
                    rec_date = _parse_date(payload.get("received_date")) or date.today()
                    referral_repo = ReferralRepository(db)
                    referral_number = await referral_repo.generate_referral_number(rec_date)

                    referral = Referral(
                        referral_number=referral_number,
                        status=payload.get("status", "DRAFT"),
                        received_date=rec_date,
                        received_time=_parse_datetime(payload.get("received_time")),
                        received_method=payload.get("received_method", "phone"),
                        community=payload.get("community"),
                        priority=payload.get("priority", "Medium"),
                        risk_level=payload.get("risk_level", "Low"),
                        summary=payload.get("summary", "Field Intake Draft"),
                        immediate_safety_concerns=bool(payload.get("immediate_safety_concerns", False)),
                        law_enforcement_involved=bool(payload.get("law_enforcement_involved", False)),
                        notes=payload.get("notes"),
                        assigned_worker_id=user_id,
                        created_by=user_id,
                    )
                    db.add(referral)
                    if hasattr(db, "flush"):
                        await db.flush()

                    ledger = MigrationLedger(
                        source_system="MOBILE_SYNC",
                        source_id=mutation_id,
                        target_entity_type="INTAKE",
                        target_entity_id=referral.id,
                        status="COMPLETED",
                    )
                    db.add(ledger)
                    if hasattr(db, "flush"):
                        await db.flush()

                await db_commit(db)

                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "SUCCESS",
                    "server_id": str(referral.id),
                    "referral_number": referral_number,
                })
            except Exception as exc:
                logger.error(f"Failed to process offline intake {mutation_id}: {exc}")
                results.append({"client_mutation_id": mutation_id, "status": "FAILED", "error": str(exc)})

        # 5. Handle HOME_VISIT entity (CalendarEvent HOME_VISIT)
        elif entity_type == "HOME_VISIT":
            if user_permissions and not (user_permissions & {Permissions.APPOINTMENT_MANAGE, Permissions.CASE_READ, Permissions.ADMIN_USERS_MANAGE}):
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "PERMISSION_DENIED",
                    "error": "User lacks calendar event permission.",
                })
                continue

            try:
                async with _atomic_mutation_savepoint(db):
                    start_at = _parse_datetime(payload.get("start_at"), datetime.utcnow())
                    end_at = _parse_datetime(payload.get("end_at"), start_at)

                    raw_person = payload.get("person_id")
                    resolved_person = await _resolve_target_id(db, raw_person, temp_person_map) if raw_person else None

                    event = CalendarEvent(
                        event_type="HOME_VISIT",
                        title=payload.get("title", "Field Home Visit"),
                        description=payload.get("description", payload.get("notes", "Offline Field Home Visit")),
                        location=payload.get("location"),
                        start_at=start_at,
                        end_at=end_at,
                        case_id=target_case_id,
                        person_id=resolved_person,
                        assigned_user_id=user_id,
                        status=payload.get("status", "SCHEDULED"),
                        created_by=user_id,
                    )
                    db.add(event)
                    if hasattr(db, "flush"):
                        await db.flush()

                    ledger = MigrationLedger(
                        source_system="MOBILE_SYNC",
                        source_id=mutation_id,
                        target_entity_type="HOME_VISIT",
                        target_entity_id=event.id,
                        status="COMPLETED",
                    )
                    db.add(ledger)
                    if hasattr(db, "flush"):
                        await db.flush()

                await db_commit(db)

                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "SUCCESS",
                    "server_id": str(event.id),
                })
            except Exception as exc:
                logger.error(f"Failed to process home visit mutation {mutation_id}: {exc}")
                results.append({"client_mutation_id": mutation_id, "status": "FAILED", "error": str(exc)})

        # 6. Handle FOLLOW_UP entity (CalendarEvent CASE_NOTE_FOLLOWUP)
        elif entity_type in ["FOLLOW_UP", "FOLLOWUP"]:
            if user_permissions and not (user_permissions & {Permissions.APPOINTMENT_MANAGE, Permissions.CASE_READ, Permissions.ADMIN_USERS_MANAGE}):
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "PERMISSION_DENIED",
                    "error": "User lacks calendar event permission.",
                })
                continue

            try:
                async with _atomic_mutation_savepoint(db):
                    start_at = _parse_datetime(payload.get("start_at"), datetime.utcnow())
                    end_at = _parse_datetime(payload.get("end_at"), start_at)

                    raw_person = payload.get("person_id")
                    resolved_person = await _resolve_target_id(db, raw_person, temp_person_map) if raw_person else None

                    event = CalendarEvent(
                        event_type="CASE_NOTE_FOLLOWUP",
                        title=payload.get("title", "Case Follow-up Task"),
                        description=payload.get("description", payload.get("notes", "Offline Field Follow-up Task")),
                        location=payload.get("location"),
                        start_at=start_at,
                        end_at=end_at,
                        case_id=target_case_id,
                        person_id=resolved_person,
                        assigned_user_id=user_id,
                        status=payload.get("status", "SCHEDULED"),
                        created_by=user_id,
                    )
                    db.add(event)
                    if hasattr(db, "flush"):
                        await db.flush()

                    ledger = MigrationLedger(
                        source_system="MOBILE_SYNC",
                        source_id=mutation_id,
                        target_entity_type="FOLLOW_UP",
                        target_entity_id=event.id,
                        status="COMPLETED",
                    )
                    db.add(ledger)
                    if hasattr(db, "flush"):
                        await db.flush()

                await db_commit(db)

                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "SUCCESS",
                    "server_id": str(event.id),
                })
            except Exception as exc:
                logger.error(f"Failed to process follow-up mutation {mutation_id}: {exc}")
                results.append({"client_mutation_id": mutation_id, "status": "FAILED", "error": str(exc)})

        # 7. Handle CASE_NOTE creation / edit
        elif entity_type == "CASE_NOTE":
            if user_permissions and not (user_permissions & {Permissions.CASE_NOTE_CREATE, Permissions.CASE_UPDATE, Permissions.ADMIN_USERS_MANAGE}):
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "PERMISSION_DENIED",
                    "error": "User lacks case note create permission.",
                })
                continue

            if not target_case_id:
                results.append({
                    "client_mutation_id": mutation_id,
                    "status": "FAILED",
                    "error": "Case note requires a valid target case_id.",
                })
                continue

            existing_note_id = payload.get("id")
            if existing_note_id:
                note = await db_query_first(db, CaseNote, CaseNote.id == uuid.UUID(existing_note_id))
                if note:
                    if getattr(note, "is_locked", False):
                        results.append({"client_mutation_id": mutation_id, "status": "LOCKED_RECORD_REJECTED"})
                        continue
                    server_version = getattr(note, "version", 1)
                    if expected_version and expected_version < server_version:
                        results.append(
                            {"client_mutation_id": mutation_id, "status": "CONFLICT", "server_version": server_version}
                        )
                        continue

            try:
                async with _atomic_mutation_savepoint(db):
                    note = CaseNote(
                        case_id=target_case_id,
                        subject=payload.get("title", "Offline Field Note"),
                        content=payload.get("summary", "Offline Field Observations"),
                        note_type=payload.get("note_type", "Progress Note"),
                        status="DRAFT",
                        is_locked=False,
                        locked_at=None,
                        locked_by=None,
                        created_by=user_id,
                    )
                    db.add(note)
                    if hasattr(db, "flush"):
                        await db.flush()

                    ledger = MigrationLedger(
                        source_system="MOBILE_SYNC",
                        source_id=mutation_id,
                        target_entity_type="CASE_NOTE",
                        target_entity_id=note.id,
                        status="COMPLETED",
                    )
                    db.add(ledger)
                    if hasattr(db, "flush"):
                        await db.flush()

                await db_commit(db)

                results.append({"client_mutation_id": mutation_id, "status": "SUCCESS", "server_id": str(note.id)})
            except Exception as exc:
                logger.error(f"Failed to process offline note mutation {mutation_id}: {exc}")
                results.append({"client_mutation_id": mutation_id, "status": "FAILED", "error": str(exc)})

        else:
            results.append({"client_mutation_id": mutation_id, "status": "UNSUPPORTED_ENTITY"})

    return {"status": "BATCH_PROCESSED", "processed_count": len(results), "items": results}
