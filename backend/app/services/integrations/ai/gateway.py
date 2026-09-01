"""Ask Red Bear Centralized AI Gateway & Authorization-First Context Manager."""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.case import Case
from app.models.case_management import CaseAssignment, CaseRestriction
from app.models.integrations import AiRequestAudit
from app.permissions.constants import Permissions
from app.services.integrations.ai.base import AiProvider
from app.services.integrations.ai.fake_provider import FakeAiProvider
from app.services.integrations.ai.prompt_guard import inspect_prompt_safety
from app.services.integrations.ai.tools import execute_ai_tool
from app.services.integrations.utils import db_commit, db_query_all

logger = logging.getLogger(__name__)


class AiGateway:
    """Centralized AI Gateway enforcing Auth-First context, field redactions, and prompt security."""

    @staticmethod
    async def get_authorized_case_ids(db: Any, user_id: uuid.UUID, user_permissions: set[str]) -> list[uuid.UUID]:
        """Retrieve case IDs authorized for the given user, respecting Case Restrictions."""
        # Check active restrictions
        restrictions = await db_query_all(
            db, CaseRestriction, CaseRestriction.user_id == user_id, CaseRestriction.is_active
        )
        restricted_set = {r.case_id for r in restrictions}

        # If user has explicit case.read permission
        if Permissions.CASE_READ in user_permissions:
            all_cases = await db_query_all(db, Case)
            return [c.id for c in all_cases if c.id not in restricted_set]

        # Assigned cases only
        assignments = await db_query_all(
            db, CaseAssignment, CaseAssignment.user_id == user_id, CaseAssignment.is_active
        )
        return [a.case_id for a in assignments if a.case_id not in restricted_set]

    @staticmethod
    async def process_ai_request(
        db: Any,
        user_id: uuid.UUID,
        user_permissions: set[str],
        prompt: str,
        case_id: uuid.UUID | None = None,
        provider: AiProvider | None = None,
    ) -> dict[str, Any]:
        """Execute Ask Red Bear AI request behind strict authorization and field redaction."""
        if provider is None:
            provider = FakeAiProvider()

        # Step 1: Prompt Safety Inspection
        is_safe, safety_msg = inspect_prompt_safety(prompt)
        if not is_safe:
            return {
                "content": f"⚠️ Ask Red Bear Security Notice: {safety_msg}",
                "sources": [],
                "is_error": True,
            }

        # Step 2: Authorization-First Context Construction
        authorized_case_ids = await AiGateway.get_authorized_case_ids(db, user_id, user_permissions)

        if case_id and case_id not in authorized_case_ids:
            # User is restricted or unauthorized for requested case!
            return {
                "content": "⚠️ Ask Red Bear Access Denied: You do not have permission to view records for the requested case.",
                "sources": [],
                "is_error": True,
            }

        # Step 3: Classify Intent & Execute Allowlisted Tool
        intent_data = await provider.classify_intent_and_tool(prompt)
        tool_name = intent_data.get("tool", "get_case_summary")
        tool_params = intent_data.get("parameters", {})
        if case_id:
            tool_params["case_id"] = str(case_id)

        context_documents = []
        try:
            if tool_name in ["get_case_summary", "get_my_cases", "get_overdue_goals", "search_authorized_clients"]:
                context_documents = await execute_ai_tool(db, tool_name, tool_params, user_id, authorized_case_ids)
        except Exception as exc:
            logger.warning(f"AI Tool execution warning: {exc}")

        # Step 4: Redaction Engine (Field Security)
        redacted_docs = []
        for doc in context_documents:
            clean_doc = dict(doc)
            if Permissions.CLIENT_MEDICAL_READ not in user_permissions:
                clean_doc.pop("medical_notes", None)
                clean_doc.pop("allergies", None)
            if Permissions.INTAKE_REPORTER_READ not in user_permissions:
                clean_doc.pop("reporter_name", None)
                clean_doc.pop("reporter_phone", None)
            if Permissions.FINANCE_REQUEST_READ not in user_permissions:
                clean_doc.pop("budget", None)
                clean_doc.pop("amount", None)
            redacted_docs.append(clean_doc)

        # Step 5: Model Completion
        start_time = datetime.utcnow()
        completion = await provider.generate_completion(
            prompt=prompt,
            context_documents=redacted_docs,
            system_instruction="You are Ask Red Bear AI, an assistive assistant for CRBCL Family Wellness.",
        )
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Step 6: Audit Logging
        audit_entry = AiRequestAudit(
            user_id=user_id,
            provider_key="AI_RED_BEAR",
            model_name=completion.get("model", "FakeClaude"),
            intent_tool=tool_name,
            case_id=case_id,
            prompt_tokens=completion.get("prompt_tokens", 0),
            completion_tokens=completion.get("completion_tokens", 0),
            latency_ms=latency_ms,
            estimated_cost_cad=Decimal("0.0015"),
            is_success=True,
        )
        db.add(audit_entry)
        await db_commit(db)

        return {
            "content": completion.get("content", ""),
            "sources": completion.get("sources", []),
            "model": completion.get("model"),
            "tool_used": tool_name,
            "is_error": False,
        }
