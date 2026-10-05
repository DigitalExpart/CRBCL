"""API Router for Ask Red Bear AI Assistant & Cost Audits."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.integrations import AiRequestAudit
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.services.integrations.ai.gateway import AiGateway
from app.services.speech_service import SpeechService

router = APIRouter(prefix="/ask-red-bear", tags=["ask-red-bear"])


class AskRedBearQueryRequest(BaseModel):
    prompt: str
    case_id: uuid.UUID | None = None


@router.post("/query", response_model=dict[str, Any])
async def query_ask_red_bear(
    payload: AskRedBearQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute Ask Red Bear AI query behind Auth-First context manager and field redactions."""
    perm_service = PermissionService(db)
    user_perms = await perm_service.get_user_permissions(current_user.id)
    if not user_perms and hasattr(current_user, "roles"):
        try:
            user_perms = {
                p.permission if hasattr(p, "permission") else getattr(p, "key", str(p))
                for r in current_user.roles
                for p in getattr(r, "permissions", [])
            }
        except Exception:
            pass

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


@router.get("/transcribe/status")
async def get_ask_red_bear_transcription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return availability and readiness of the speech-to-text service for Ask Red Bear."""
    perm_service = PermissionService(db)
    has_ai_query = await perm_service.user_has_permission(current_user.id, Permissions.AI_QUERY)
    has_case_read = await perm_service.user_has_permission(current_user.id, Permissions.CASE_READ)
    if not has_ai_query and not has_case_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "PERMISSION_DENIED", "message": "User lacks required permissions to access Ask Red Bear."}},
        )

    service = SpeechService(db)
    return service.get_status()


@router.post("/transcribe")
async def transcribe_ask_red_bear_audio(
    response: Response,
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    case_id: uuid.UUID | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe in-memory audio recording for prompt drafting in Ask Red Bear.

    INPUT AID ONLY:
    - Transcribe != Query Ask Red Bear.
    - NEVER executes an AI query, tool, or completion.
    - NEVER saves a Case Note, Intake, or Client record.
    - NEVER persists raw audio or transcript narrative.
    - Transient processing returning text transcript only.
    - User reviews/edits transcript in browser and explicitly presses Send.
    """
    perm_service = PermissionService(db)
    has_ai_query = await perm_service.user_has_permission(current_user.id, Permissions.AI_QUERY)
    has_case_read = await perm_service.user_has_permission(current_user.id, Permissions.CASE_READ)
    if not has_ai_query and not has_case_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "PERMISSION_DENIED", "message": "User lacks required permissions to access Ask Red Bear."}},
        )

    audio_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"

    speech_service = SpeechService(db)
    result = await speech_service.transcribe_ask_red_bear_audio(
        audio_bytes=audio_bytes,
        content_type=content_type,
        current_user=current_user,
        language=language,
        case_id=case_id,
    )

    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"

    return result



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
