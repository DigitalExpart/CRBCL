"""Local filesystem storage provider implementation for development."""

from __future__ import annotations

from pathlib import Path

from app.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, storage_path: str) -> Path:
        clean_path = storage_path.lstrip("/").replace("..", "")
        return self.base_dir / clean_path

    async def upload(self, storage_path: str, data: bytes, content_type: str) -> str:
        target = self._resolve_path(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return str(target)

    async def download(self, storage_path: str) -> bytes:
        target = self._resolve_path(storage_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        return target.read_bytes()

    async def delete(self, storage_path: str) -> bool:
        target = self._resolve_path(storage_path)
        if target.exists():
            target.unlink()
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        return self._resolve_path(storage_path).exists()

    async def generate_signed_url(self, storage_path: str, expires_in_seconds: int = 300) -> str:
        # For local development, returns an API route download endpoint
        return f"/api/v1/documents/download/{storage_path}"
