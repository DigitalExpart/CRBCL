"""API Router for OCR Document Processing & Human Field Verification."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.integrations import OcrJob
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.integrations.ocr.ocr_service import (
    confirm_ocr_field,
    create_ocr_job,
    process_ocr_job,
)

router = APIRouter(prefix="/ocr", tags=["ocr"])


class OcrUploadRequest(BaseModel):
    document_name: str
    document_url: str


class OcrConfirmRequest(BaseModel):
    target_entity_type: str  # CLIENT, etc.
    target_entity_id: uuid.UUID
    confirmed_fields: dict[str, Any]


@router.post("/jobs", response_model=dict[str, Any])
async def submit_ocr_job(
    payload: OcrUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit document for OCR text extraction and candidate field generation."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.OCR_PROCESS not in user_perms and Permissions.DOCUMENT_UPLOAD not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to process OCR documents.",
        )

    job = create_ocr_job(
        db=db,
        document_name=payload.document_name,
        document_url=payload.document_url,
        requested_by_id=current_user.id,
    )

    # Process async
    updated_job = await process_ocr_job(db=db, job_id=job.id)

    return {
        "job_id": str(updated_job.id),
        "document_name": updated_job.document_name,
        "status": updated_job.status,
        "extracted_text": updated_job.extracted_text,
        "candidate_fields": updated_job.candidate_fields_json,
    }


@router.get("/jobs/{job_id}", response_model=dict[str, Any])
def get_ocr_job_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status and draft candidate fields of an OCR processing job."""
    job = db.query(OcrJob).filter(OcrJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR Job not found.")

    return {
        "job_id": str(job.id),
        "document_name": job.document_name,
        "status": job.status,
        "extracted_text": job.extracted_text,
        "candidate_fields_json": job.candidate_fields_json,
        "error_message": job.error_message,
    }


@router.post("/jobs/{job_id}/confirm", response_model=dict[str, Any])
def confirm_ocr_candidate_fields(
    job_id: uuid.UUID,
    payload: OcrConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply human-verified OCR draft fields to target authoritative record."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.OCR_CONFIRM not in user_perms and Permissions.CLIENT_UPDATE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to confirm OCR candidate fields.",
        )

    try:
        res = confirm_ocr_field(
            db=db,
            job_id=job_id,
            user_permissions=user_perms,
            target_entity_type=payload.target_entity_type,
            target_entity_id=payload.target_entity_id,
            confirmed_fields=payload.confirmed_fields,
        )
        return res
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
