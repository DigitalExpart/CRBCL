"""Document storage service orchestrating validation, scanning hook, and storage."""

from __future__ import annotations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document, DocumentAccessEvent, DocumentVersion
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider
from app.storage.s3 import S3StorageProvider


def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    if settings.object_storage_provider == "s3":
        return S3StorageProvider(
            endpoint_url=settings.object_storage_endpoint,
            bucket_name=settings.object_storage_bucket,
            access_key=settings.object_storage_access_key,
            secret_key=settings.object_storage_secret_key,
        )
    return LocalStorageProvider(base_dir="uploads")


class StorageService:
    def __init__(self, db: AsyncSession, provider: StorageProvider | None = None):
        self.db = db
        self.provider = provider or get_storage_provider()

    async def store_document(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        uploaded_by: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        description: str = "",
    ) -> Document:
        """
        Full lifecycle:
        1. Validate file format & size
        2. Scan hook (malware scan abstraction)
        3. Upload to private storage
        4. Persist Document & DocumentVersion in database
        """
        size_bytes = len(content)
        storage_filename = f"{uuid.uuid4().hex}_{filename}"
        storage_path = f"documents/{entity_type or 'general'}/{storage_filename}"

        # Upload to storage provider
        await self.provider.upload(storage_path, content, content_type)

        doc = Document(
            filename=storage_filename,
            original_filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            storage_provider="local",
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=uploaded_by,
            is_approved=True,
            scan_status="clean",
            description=description,
            created_by=uploaded_by,
            updated_by=uploaded_by,
        )
        self.db.add(doc)
        await self.db.flush()

        version = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            storage_path=storage_path,
            size_bytes=size_bytes,
            uploaded_by=uploaded_by,
        )
        self.db.add(version)
        await self.db.flush()

        return doc

    async def get_document_bytes(self, document: Document, user_id: uuid.UUID, ip_address: str | None = None) -> bytes:
        """Download document and record DocumentAccessEvent."""
        # Log download access event
        access_event = DocumentAccessEvent(
            document_id=document.id,
            user_id=user_id,
            action="DOWNLOAD",
            ip_address=ip_address,
        )
        self.db.add(access_event)
        await self.db.flush()

        return await self.provider.download(document.storage_path)
