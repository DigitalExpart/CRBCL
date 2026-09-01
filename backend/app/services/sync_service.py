"""Mobile Sync Service handling device registration, revocation, delta pull with tombstones, and sync queue push."""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.client import Client
from app.models.device import MobileDevice
from app.models.migration import MigrationLedger
from app.permissions.constants import Permissions
from app.services.integrations.ai.gateway import AiGateway
from app.services.integrations.utils import db_commit, db_query_all, db_query_first

logger = logging.getLogger(__name__)


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
    """Validate device registration and status. Rejects revoked devices with HTTP 403."""
    if not device_id:
        return  # Allow standard web requests without device ID

    device = await db_query_first(db, MobileDevice, MobileDevice.device_id == device_id)
    if not device or device.device_status in ["REVOKED", "WIPED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_REVOKED: This device has been revoked or wiped by an administrator.",
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


async def process_sync_push(
    db: Any,
    user_id: uuid.UUID,
    user_permissions: set[str],
    push_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Process incoming offline mutation outbox queue items with idempotency and version conflict checks."""
    authorized_case_ids = await AiGateway.get_authorized_case_ids(db, user_id, user_permissions)
    results = []

    for item in push_items:
        mutation_id = item.get("client_mutation_id", str(uuid.uuid4()))
        entity_type = item.get("entity_type")
        payload = item.get("payload", {})
        expected_version = item.get("expected_version")

        # Check idempotency
        existing_ledger = await db_query_first(
            db,
            MigrationLedger,
            MigrationLedger.source_system == "MOBILE_SYNC",
            MigrationLedger.source_id == mutation_id,
        )
        if existing_ledger:
            results.append({"client_mutation_id": mutation_id, "status": "ALREADY_PROCESSED"})
            continue

        target_case_id_str = payload.get("case_id")
        if target_case_id_str:
            try:
                target_case_id = uuid.UUID(target_case_id_str)
                if target_case_id not in authorized_case_ids:
                    results.append({"client_mutation_id": mutation_id, "status": "FORBIDDEN_SCOPE"})
                    continue
            except Exception:
                results.append({"client_mutation_id": mutation_id, "status": "INVALID_CASE_ID"})
                continue

        # Handle CASE_NOTE creation / edit
        if entity_type == "CASE_NOTE":
            existing_note_id = payload.get("id")
            if existing_note_id:
                note = await db_query_first(db, CaseNote, CaseNote.id == uuid.UUID(existing_note_id))
                if note:
                    # Check locked note status
                    if getattr(note, "is_locked", False):
                        results.append({"client_mutation_id": mutation_id, "status": "LOCKED_RECORD_REJECTED"})
                        continue
                    # Check version conflict
                    server_version = getattr(note, "version", 1)
                    if expected_version and expected_version < server_version:
                        results.append(
                            {"client_mutation_id": mutation_id, "status": "CONFLICT", "server_version": server_version}
                        )
                        continue

            try:
                note = CaseNote(
                    case_id=uuid.UUID(payload["case_id"]),
                    subject=payload.get("title", "Offline Field Note"),
                    content=payload.get("summary", "Offline Field Observations"),
                    note_type=payload.get("note_type", "Progress Note"),
                    created_by=user_id,
                )
                db.add(note)
                await db_commit(db)

                # Record idempotency ledger entry
                ledger = MigrationLedger(
                    source_system="MOBILE_SYNC",
                    source_id=mutation_id,
                    target_entity_type="CASE_NOTE",
                    target_entity_id=note.id,
                    status="COMPLETED",
                )
                db.add(ledger)
                await db_commit(db)

                results.append({"client_mutation_id": mutation_id, "status": "SUCCESS", "server_id": str(note.id)})
            except Exception as exc:
                logger.error(f"Failed to process offline note mutation {mutation_id}: {exc}")
                results.append({"client_mutation_id": mutation_id, "status": "FAILED", "error": str(exc)})
        else:
            results.append({"client_mutation_id": mutation_id, "status": "UNSUPPORTED_ENTITY"})

    return {"status": "BATCH_PROCESSED", "processed_count": len(results), "items": results}
