"""Document download & secure retrieval endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.document import Document, DocumentAccessEvent
from app.services.file_security import verify_file_signature
from app.storage.service import StorageService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    request: Request,
    expires: int = Query(..., description="Signature expiration Unix timestamp"),
    sig: str = Query(..., description="HMAC-SHA256 signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a document using a short-lived cryptographically signed URL.
    Enforces HMAC verification, expiration check, and security scan status.
    Serves images inline to browser <img> tags without requiring bearer headers.
    """
    if not verify_file_signature(document_id, expires, sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired download signature.",
        )

    stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if doc.scan_status != "clean":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document failed security scan or has not been verified clean.",
        )

    storage_service = StorageService(db)
    try:
        file_bytes = await storage_service.provider.download(doc.storage_path)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file content not found in storage.",
        ) from err

    # Record access audit event
    user_id = doc.uploaded_by or doc.created_by
    if user_id:
        client_ip = request.client.host if request.client else None
        event = DocumentAccessEvent(
            document_id=doc.id,
            user_id=user_id,
            action="DOWNLOAD",
            ip_address=client_ip,
        )
        db.add(event)
        await db.commit()

    is_image = doc.content_type.lower().startswith("image/")
    disposition = "inline" if is_image else f'attachment; filename="{doc.original_filename}"'

    return Response(
        content=file_bytes,
        media_type=doc.content_type,
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "private, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )
