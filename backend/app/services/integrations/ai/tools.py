"""Ask Red Bear AI Explicit Tool Allowlist."""

import logging
import uuid
from typing import Any

from app.models.case import Case
from app.models.client import Client
from app.models.plan import PlanGoal
from app.services.integrations.utils import db_query_all, db_query_first

logger = logging.getLogger(__name__)

ALLOWED_TOOLS = {
    "get_case_summary",
    "get_my_cases",
    "get_upcoming_appointments",
    "get_overdue_goals",
    "run_approved_report",
    "search_authorized_clients",
}


async def execute_ai_tool(
    db: Any,
    tool_name: str,
    parameters: dict[str, Any],
    user_id: uuid.UUID,
    authorized_case_ids: list[uuid.UUID],
) -> list[dict[str, Any]]:
    """Execute an allowlisted AI backend query tool using strict domain authorization."""
    if tool_name not in ALLOWED_TOOLS:
        raise PermissionError(f"Tool '{tool_name}' is prohibited or not in allowlist.")

    if tool_name == "get_my_cases":
        cases = await db_query_all(db, Case, Case.id.in_(authorized_case_ids))
        return [
            {
                "case_id": str(c.id),
                "case_number": c.case_number,
                "status": c.status,
                "title": c.title,
            }
            for c in cases[:10]
        ]

    elif tool_name == "get_case_summary":
        case_id_str = parameters.get("case_id")
        if not case_id_str:
            if not authorized_case_ids:
                return []
            target_case_id = authorized_case_ids[0]
        else:
            target_case_id = uuid.UUID(case_id_str)
            if target_case_id not in authorized_case_ids:
                raise PermissionError(f"User is restricted or unauthorized for case {target_case_id}.")

        c = await db_query_first(db, Case, Case.id == target_case_id)
        if not c:
            return []
        return [
            {
                "case_id": str(c.id),
                "case_number": c.case_number,
                "title": c.title,
                "status": c.status,
                "stage": getattr(c, "stage", "INVESTIGATION"),
                "summary": f"Active case {c.case_number} under primary casework.",
            }
        ]

    elif tool_name == "get_overdue_goals":
        goals = await db_query_all(db, PlanGoal, PlanGoal.status == "OVERDUE")
        return [
            {
                "goal_id": str(g.id),
                "description": g.description,
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "status": g.status,
            }
            for g in goals[:10]
        ]

    elif tool_name == "search_authorized_clients":
        query = parameters.get("query", "")
        clients = await db_query_all(db, Client, Client.last_name.ilike(f"%{query}%"))
        return [
            {
                "client_id": str(cl.id),
                "first_name": cl.first_name,
                "last_name": cl.last_name,
            }
            for cl in clients[:5]
        ]

    return []
