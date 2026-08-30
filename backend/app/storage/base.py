"""Storage provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstract interface for document and object storage."""

    @abstractmethod
    async def upload(self, storage_path: str, data: bytes, content_type: str) -> str:
        """Upload data and return storage identifier."""
        pass

    @abstractmethod
    async def download(self, storage_path: str) -> bytes:
        """Download and return raw byte contents."""
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """Delete or quarantine object."""
        pass

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """Check if an object exists."""
        pass

    @abstractmethod
    async def generate_signed_url(self, storage_path: str, expires_in_seconds: int = 300) -> str:
        """Generate short-lived signed access URL (never permanent public URL)."""
        pass
