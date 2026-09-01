"""API Router for Ask Red Bear AI Assistant & Cost Audits."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.integrations import AiRequestAudit
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.integrations.ai.gateway import AiGateway

router = APIRouter(prefix="/ask-red-bear", tags=["ask-red-bear"])


class AskRedBearQueryRequest(BaseModel):
    prompt: str
    case_id: uuid.UUID | None = None


@router.post("/query", response_model=dict[str, Any])
async def query_ask_red_bear(
    payload: AskRedBearQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute Ask Red Bear AI query behind Auth-First context manager and field redactions."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.AI_QUERY not in user_perms and Permissions.CASE_READ not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to access Ask Red Bear AI.",
        )

    res = await AiGateway.process_ai_request(
        db=db,
        user_id=current_user.id,
        user_permissions=user_perms,
        prompt=payload.prompt,
        case_id=payload.case_id,
    )
    return res


@router.get("/audits", response_model=list[dict[str, Any]])
def get_ai_request_audits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve audit log of AI queries, latency, and estimated token costs (Admin view)."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.INTEGRATION_READ not in user_perms and Permissions.ADMIN_CONFIGURATION_MANAGE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to view AI request audit metrics.",
        )

    records = db.query(AiRequestAudit).order_by(AiRequestAudit.created_at.desc()).limit(50).all()
    return [
        {
            "audit_id": str(r.id),
            "user_id": str(r.user_id),
            "provider_key": r.provider_key,
            "model_name": r.model_name,
            "intent_tool": r.intent_tool,
            "case_id": str(r.case_id) if r.case_id else None,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "latency_ms": r.latency_ms,
            "estimated_cost_cad": float(r.estimated_cost_cad),
            "is_success": r.is_success,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
