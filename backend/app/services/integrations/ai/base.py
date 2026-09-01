"""Abstract Base Provider for Ask Red Bear AI Engine."""

from abc import ABC, abstractmethod
from typing import Any


class AiProvider(ABC):
    """Abstract interface defining AI capabilities."""

    @abstractmethod
    async def generate_completion(
        self, prompt: str, context_documents: list[dict[str, Any]], system_instruction: str
    ) -> dict[str, Any]:
        """Generate text completion from LLM model."""
        pass

    @abstractmethod
    async def classify_intent_and_tool(self, user_question: str) -> dict[str, Any]:
        """Classify user query into approved tool calls."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Run health check against AI model endpoint."""
        pass
