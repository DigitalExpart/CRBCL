"""Synthetic Fake AI Provider for Offline Development & Security Testing."""

from typing import Any

from app.services.integrations.ai.base import AiProvider


class FakeAiProvider(AiProvider):
    """Synthetic AI provider for Ask Red Bear."""

    def __init__(self, fail_mode: bool = False):
        self.fail_mode = fail_mode

    async def generate_completion(
        self, prompt: str, context_documents: list[dict[str, Any]], system_instruction: str
    ) -> dict[str, Any]:
        if self.fail_mode:
            raise RuntimeError("AI Provider model request timeout")

        doc_count = len(context_documents)
        return {
            "content": (
                "⚠️ AI GENERATED — REQUIRES HUMAN REVIEW\n\n"
                f"Based on {doc_count} authorized records retrieved for your request: "
                f"Summary of case activity for query '{prompt[:50]}'. All actions require caseworker verification."
            ),
            "model": "FakeClaude35Sonnet",
            "prompt_tokens": 150,
            "completion_tokens": 80,
            "latency_ms": 45,
            "sources": [doc.get("title", f"Record #{i+1}") for i, doc in enumerate(context_documents)],
        }

    async def classify_intent_and_tool(self, user_question: str) -> dict[str, Any]:
        if self.fail_mode:
            raise RuntimeError("AI Provider model request timeout")

        q_lower = user_question.lower()
        if "summary" in q_lower or "case" in q_lower:
            return {"tool": "get_case_summary", "parameters": {}}
        elif "my cases" in q_lower:
            return {"tool": "get_my_cases", "parameters": {}}
        elif "appointment" in q_lower or "calendar" in q_lower:
            return {"tool": "get_upcoming_appointments", "parameters": {}}
        elif "report" in q_lower:
            return {"tool": "run_approved_report", "parameters": {}}
        elif "client" in q_lower or "search" in q_lower:
            return {"tool": "search_authorized_clients", "parameters": {}}
        return {"tool": "general_qa", "parameters": {}}

    async def health_check(self) -> dict[str, Any]:
        if self.fail_mode:
            return {"status": "ERROR", "message": "AI Provider unreachable"}
        return {"status": "OK", "provider": "FakeAiProvider"}
