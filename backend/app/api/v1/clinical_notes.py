"""FastAPI router for Clinical / LPN Notes with strict RBAC permission gating."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.services.sprint_b_service import SprintBService

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])


class ClinicalNoteCreate(BaseModel):
    client_id: str = Field(..., description="Target client UUID")
    case_id: str | None = Field(None, description="Optional case UUID")
    note_type: str = Field("LPN_OBSERVATION", description="Clinical note category")
    subject: str = Field(..., max_length=255, description="Note subject heading")
    narrative: str = Field(..., description="Clinical narrative content")
    confidentiality: str = Field("CONFIDENTIAL", description="Confidentiality tier")


class ClinicalAddendumCreate(BaseModel):
    narrative: str = Field(..., description="Addendum text")


@router.post("", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_clinical_note(
    req: ClinicalNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.CLINICAL_NOTE_CREATE)),
):
    """Create a new draft Clinical / LPN note (LPN / Medical staff only)."""
    service = SprintBService(db)
    note = await service.create_clinical_note(req.model_dump(), author_id=current_user.id)
    return {
        "status": "SUCCESS",
        "id": str(note.id),
        "client_id": str(note.client_id),
        "note_type": note.note_type,
        "note_status": note.status,
    }


@router.get("/client/{client_id}", response_model=list[dict[str, Any]])
async def list_clinical_notes_for_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.CLINICAL_NOTE_READ)),
):
    """List clinical notes for a client (Requires clinical read permission)."""
    service = SprintBService(db)
    notes = await service.list_clinical_notes_for_client(uuid.UUID(client_id))
    return [
        {
            "id": str(n.id),
            "client_id": str(n.client_id),
            "case_id": str(n.case_id) if n.case_id else None,
            "author_id": str(n.author_id),
            "note_type": n.note_type,
            "subject": n.subject,
            "narrative": n.narrative,
            "confidentiality": n.confidentiality,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
            "locked_at": n.locked_at.isoformat() if n.locked_at else None,
            "addenda": [
                {
                    "id": str(a.id),
                    "author_id": str(a.author_id),
                    "narrative": a.narrative,
                    "created_at": a.created_at.isoformat(),
                }
                for a in n.addenda
            ],
        }
        for n in notes
    ]


@router.post("/{note_id}/lock", response_model=dict[str, Any])
async def lock_clinical_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.CLINICAL_NOTE_LOCK)),
):
    """Lock a completed clinical note to prevent further edits (Immutable)."""
    service = SprintBService(db)
    note = await service.lock_clinical_note(uuid.UUID(note_id), user_id=current_user.id)
    return {"status": "LOCKED", "id": str(note.id), "locked_at": note.locked_at.isoformat()}


@router.post("/{note_id}/addenda", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def add_clinical_addendum(
    note_id: str,
    req: ClinicalAddendumCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.CLINICAL_NOTE_CREATE)),
):
    """Attach an addendum to a locked clinical note."""
    service = SprintBService(db)
    addendum = await service.add_clinical_addendum(uuid.UUID(note_id), req.narrative, author_id=current_user.id)
    return {"status": "SUCCESS", "id": str(addendum.id), "clinical_note_id": str(addendum.clinical_note_id)}


@router.get("/{note_id}/export", response_model=dict[str, Any])
async def export_clinical_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.CLINICAL_NOTE_EXPORT)),
):
    """Export clinical note metadata and narrative for authorized clinical reporting."""
    service = SprintBService(db)
    note = await service.get_clinical_note(uuid.UUID(note_id))
    return {
        "export_status": "AUTHORIZED",
        "id": str(note.id),
        "subject": note.subject,
        "narrative": note.narrative,
        "confidentiality": note.confidentiality,
    }
