"""OCR Asynchronous Job Service & Human Verification Engine."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from app.models.client import Client
from app.models.integrations import OcrJob
from app.permissions.constants import Permissions
from app.services.integrations.ocr.base import OcrProvider
from app.services.integrations.ocr.fake_provider import FakeOcrProvider
from app.services.integrations.utils import db_commit, db_query_first, db_refresh

logger = logging.getLogger(__name__)


async def create_ocr_job(
    db: Any,
    document_name: str,
    document_url: str,
    requested_by_id: uuid.UUID | None = None,
) -> OcrJob:
    """Create a new OCR Document Processing Job in PENDING status."""
    job = OcrJob(
        document_name=document_name,
        document_url=document_url,
        provider_key="TESSERACT",
        status="PENDING",
        requested_by_id=requested_by_id,
    )
    db.add(job)
    await db_commit(db)
    await db_refresh(db, job)
    return job


async def process_ocr_job(db: Any, job_id: uuid.UUID, provider: OcrProvider | None = None) -> OcrJob:
    """Execute asynchronous OCR text extraction and candidate field generation."""
    job = await db_query_first(db, OcrJob, OcrJob.id == job_id)
    if not job:
        raise ValueError(f"OCR Job {job_id} not found.")

    if provider is None:
        provider = FakeOcrProvider()

    job.status = "PROCESSING"
    await db_commit(db)

    try:
        raw_text = await provider.extract_text(job.document_url)
        fields_data = await provider.extract_fields(job.document_url)

        job.extracted_text = raw_text
        job.candidate_fields_json = json.dumps(fields_data)
        job.status = "REVIEW_REQUIRED"
        job.updated_at = datetime.utcnow()
        await db_commit(db)
        await db_refresh(db, job)
        return job
    except Exception as exc:
        logger.error(f"OCR Job {job_id} failed: {exc}")
        job.status = "FAILED"
        job.error_message = str(exc)
        job.updated_at = datetime.utcnow()
        await db_commit(db)
        await db_refresh(db, job)
        return job


async def confirm_ocr_field(
    db: Any,
    job_id: uuid.UUID,
    user_permissions: set[str],
    target_entity_type: str,
    target_entity_id: uuid.UUID,
    confirmed_fields: dict[str, Any],
) -> dict[str, Any]:
    """Apply human-verified OCR candidate fields to authoritative domain record.

    Guarantees:
    - Enforces target field write permission (e.g., client.identifiers.write).
    - Requires explicit human review before mutating authoritative DB.
    """
    job = await db_query_first(db, OcrJob, OcrJob.id == job_id)
    if not job:
        raise ValueError(f"OCR Job {job_id} not found.")

    if target_entity_type.upper() == "CLIENT":
        if (
            Permissions.CLIENT_IDENTIFIERS_WRITE not in user_permissions
            and Permissions.CLIENT_UPDATE not in user_permissions
        ):
            raise PermissionError("User lacks required client.identifiers.write permission to confirm OCR fields.")

        client = await db_query_first(db, Client, Client.id == target_entity_id)
        if not client:
            raise ValueError(f"Client {target_entity_id} not found.")

        # Apply confirmed fields
        if "first_name" in confirmed_fields:
            client.first_name = confirmed_fields["first_name"]
        if "last_name" in confirmed_fields:
            client.last_name = confirmed_fields["last_name"]
        if "health_card_number" in confirmed_fields:
            client.health_card_number = confirmed_fields["health_card_number"]

        job.status = "CONFIRMED"
        job.updated_at = datetime.utcnow()
        await db_commit(db)
        return {"status": "CONFIRMED", "client_id": str(client.id), "updated_fields": list(confirmed_fields.keys())}

    raise NotImplementedError(f"Target entity type '{target_entity_type}' not supported for OCR confirmation.")
