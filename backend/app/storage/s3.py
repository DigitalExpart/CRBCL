"""S3-compatible object storage provider stub."""

from __future__ import annotations

from app.storage.base import StorageProvider


class S3StorageProvider(StorageProvider):
    def __init__(
        self,
        endpoint_url: str | None = None,
        bucket_name: str = "crbcl-documents",
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key

    async def upload(self, storage_path: str, data: bytes, content_type: str) -> str:
        # Phase 1 adapter stub — ready for botocore / aioboto3 wire-up in cloud deployment
        raise NotImplementedError("S3 storage provider is configured for production cloud deployment")

    async def download(self, storage_path: str) -> bytes:
        raise NotImplementedError("S3 storage provider is configured for production cloud deployment")

    async def delete(self, storage_path: str) -> bool:
        raise NotImplementedError("S3 storage provider is configured for production cloud deployment")

    async def exists(self, storage_path: str) -> bool:
        raise NotImplementedError("S3 storage provider is configured for production cloud deployment")

    async def generate_signed_url(self, storage_path: str, expires_in_seconds: int = 300) -> str:
        raise NotImplementedError("S3 storage provider is configured for production cloud deployment")
