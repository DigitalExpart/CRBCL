"""Abstract Base Provider for OCR Document Processing."""

from abc import ABC, abstractmethod
from typing import Any


class OcrProvider(ABC):
    """Abstract interface defining OCR capabilities."""

    @abstractmethod
    async def extract_text(self, document_url: str) -> str:
        """Extract raw text string from document image/PDF."""
        pass

    @abstractmethod
    async def extract_fields(self, document_url: str) -> dict[str, Any]:
        """Extract structured candidate key-value pairs with confidence scores."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Run health check on OCR engine."""
        pass
