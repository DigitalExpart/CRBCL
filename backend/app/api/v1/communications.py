"""API Router for Public Communications Posts (Social Media Integration Foundation)."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.integrations import CommunicationsPost
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.integrations.communications.communications_service import (
    approve_communications_post,
    create_communications_post,
    publish_communications_post,
)

router = APIRouter(prefix="/communications", tags=["communications"])


class CommunicationsPostCreateRequest(BaseModel):
    title: str
    content: str
    target_platforms: str = "META"


@router.get("/posts", response_model=list[dict[str, Any]])
def list_communications_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List public communications outreach posts."""
    posts = db.query(CommunicationsPost).order_by(CommunicationsPost.created_at.desc()).all()
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "content": p.content,
            "target_platforms": p.target_platforms,
            "status": p.status,
            "created_by_id": str(p.created_by_id),
            "approved_by_id": str(p.approved_by_id) if p.approved_by_id else None,
            "published_at": p.published_at.isoformat() if p.published_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in posts
    ]


@router.post("/posts", response_model=dict[str, Any])
def draft_communications_post(
    payload: CommunicationsPostCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Draft new public community announcement post."""
    post = create_communications_post(
        db=db,
        title=payload.title,
        content=payload.content,
        created_by_id=current_user.id,
        target_platforms=payload.target_platforms,
    )
    return {"status": "SUCCESS", "post_id": str(post.id), "post_status": post.status}


@router.post("/posts/{post_id}/approve", response_model=dict[str, Any])
def approve_post(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a drafted communications post for social publication."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.COMMUNICATIONS_MANAGE not in user_perms and Permissions.ADMIN_CONFIGURATION_MANAGE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to approve public communications posts.",
        )
    try:
        updated = approve_communications_post(db=db, post_id=post_id, approved_by_id=current_user.id)
        return {"status": "APPROVED", "post_id": str(updated.id)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/posts/{post_id}/publish", response_model=dict[str, Any])
async def publish_post(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publish approved post to external social channel."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.COMMUNICATIONS_MANAGE not in user_perms and Permissions.ADMIN_CONFIGURATION_MANAGE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to publish communications posts.",
        )
    try:
        res = await publish_communications_post(db=db, post_id=post_id)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
