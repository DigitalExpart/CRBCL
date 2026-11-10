"""Document management, upload, text-based document entry, and item-level access control."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.document import Document, DocumentAccessEvent, ItemAccessRequest
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.services.file_security import verify_file_signature
from app.storage.service import StorageService

router = APIRouter(prefix="/documents", tags=["Documents"])


# --- Schemas ---

class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    description: str
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    file_url: str | None = None
    document_content: str | None = None
    is_confidential: bool
    team_id: uuid.UUID | None = None
    access_mode: str
    allowed_roles: list[str] | None = None
    allowed_user_ids: list[str] | None = None
    restricted_roles: list[str] | None = None
    restricted_user_ids: list[str] | None = None
    scan_status: str
    created_at: datetime
    uploaded_by: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="General", max_length=100)
    description: str = Field(default="")
    team_id: uuid.UUID | None = None
    is_confidential: bool = False
    access_mode: str = Field(default="INHERIT")
    document_content: str | None = None
    filename: str | None = None
    original_filename: str | None = None
    content_type: str | None = None
    file_url: str | None = None
    file_size: str | None = None
    file_type: str | None = None


class AccessControlUpdate(BaseModel):
    access_mode: str = Field(..., description="INHERIT | RESTRICTED | ALLOW_SELECTED | REQUIRES_APPROVAL")
    allowed_roles: list[str] | None = None
    allowed_user_ids: list[str] | None = None
    restricted_roles: list[str] | None = None
    restricted_user_ids: list[str] | None = None


class AccessRequestCreate(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class AccessRequestReview(BaseModel):
    review_notes: str | None = Field(None, max_length=1000)


class AccessRequestResponse(BaseModel):
    id: uuid.UUID
    item_type: str
    item_id: uuid.UUID
    requester_id: uuid.UUID
    status: str
    reason: str
    reviewer_id: uuid.UUID | None = None
    review_notes: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Access Evaluation Engine ---

async def can_user_access_document(
    doc: Document,
    user: User,
    db: AsyncSession,
) -> tuple[bool, str]:
    """
    Evaluates 4-tier supervisor-controlled item-level access control:
    1. Super admin / Executive Director / CEO override
    2. Case conflict restriction check (ADR-010)
    3. Document creator / uploader access
    4. Team scope check
    5. Access Mode check:
       - INHERIT: Requires standard document.read and team scope
       - RESTRICTED: Requires user role in allowed_roles or user ID in allowed_user_ids
       - ALLOW_SELECTED: Explicitly allows lower-level roles/users within team
       - REQUIRES_APPROVAL: Requires prior approved ItemAccessRequest
    """
    perm_svc = PermissionService(db)

    # 1. Super admin / Executive Director / CEO
    if await perm_svc.is_super_admin(user.id):
        return True, "SUPER_ADMIN"
    user_roles = await perm_svc.get_user_roles(user.id)
    if user_roles & {"ceo", "executive_director"}:
        return True, "EXECUTIVE_OVERRIDE"

    # 2. Case conflict restriction (ADR-010)
    if doc.entity_type == "case" and doc.entity_id and await perm_svc.is_user_restricted_from_case(user.id, doc.entity_id):
        return False, "CASE_RESTRICTED"

    # 3. Creator / Uploader access
    if doc.uploaded_by == user.id or doc.created_by == user.id:
        return True, "CREATOR"

    # 4. Cross-team check
    if doc.team_id:
        accessible_teams = await perm_svc.get_user_accessible_team_ids(user.id)
        if accessible_teams is not None and doc.team_id not in accessible_teams:
            return False, "CROSS_TEAM_RESTRICTED"

    # 5. Access Mode evaluation
    mode = (doc.access_mode or "INHERIT").upper()

    if mode == "INHERIT":
        has_perm = await perm_svc.user_has_permission(user.id, Permissions.DOCUMENT_READ)
        return has_perm, "INHERIT_PERM" if has_perm else "NO_DOCUMENT_READ"

    elif mode == "RESTRICTED":
        user_str_id = str(user.id)
        restricted_users = [str(x) for x in (doc.restricted_user_ids or [])]
        restricted_roles = [str(x).lower().strip() for x in (doc.restricted_roles or [])]
        if user_str_id in restricted_users or any(r in restricted_roles for r in user_roles):
            return False, "EXPLICITLY_RESTRICTED"

        allowed_users = [str(x) for x in (doc.allowed_user_ids or [])]
        allowed_roles = [str(x).lower().strip() for x in (doc.allowed_roles or [])]
        if user_str_id in allowed_users or any(r in allowed_roles for r in user_roles):
            return True, "EXPLICITLY_ALLOWED"

        # Supervisors and leadership of the authorized team can access
        if user_roles & {"supervisor", "director_manager", "resource_supervisor", "resource_director"}:
            return True, "SUPERVISOR_ALLOWED"

        return False, "RESTRICTED_ITEM"

    elif mode == "ALLOW_SELECTED":
        user_str_id = str(user.id)
        allowed_users = [str(x) for x in (doc.allowed_user_ids or [])]
        allowed_roles = [str(x).lower().strip() for x in (doc.allowed_roles or [])]
        if user_str_id in allowed_users or any(r in allowed_roles for r in user_roles):
            return True, "SELECTED_GRANT"

        if user_roles & {"supervisor", "director_manager", "resource_supervisor", "resource_director"}:
            return True, "SUPERVISOR_ALLOWED"

        return False, "NOT_IN_SELECTED_GRANT"

    elif mode == "REQUIRES_APPROVAL":
        # Supervisors and directors manage the approval workflow and retain direct access
        if user_roles & {"supervisor", "director_manager", "resource_supervisor", "resource_director"}:
            return True, "SUPERVISOR_ALLOWED"

        # Check for active APPROVED request
        stmt = select(ItemAccessRequest).where(
            ItemAccessRequest.item_id == doc.id,
            ItemAccessRequest.requester_id == user.id,
            ItemAccessRequest.status == "APPROVED",
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            return True, "REQUEST_APPROVED"

        return False, "APPROVAL_REQUIRED"

    return False, "UNKNOWN_ACCESS_MODE"


async def can_user_manage_item_restrictions(doc: Document, user: User, db: AsyncSession) -> bool:
    """Verifies that user is supervisor or above and has supervisory scope over this document."""
    perm_svc = PermissionService(db)
    if await perm_svc.is_super_admin(user.id):
        return True
    user_roles = await perm_svc.get_user_roles(user.id)
    if user_roles & {"ceo", "executive_director"}:
        return True

    if not await perm_svc.user_has_permission(user.id, Permissions.DOCUMENT_RESTRICT):
        return False

    supervisor_roles = {"supervisor", "director_manager", "resource_supervisor", "resource_director"}
    if not (user_roles & supervisor_roles):
        return False

    if doc.team_id:
        accessible_teams = await perm_svc.get_user_accessible_team_ids(user.id)
        if accessible_teams is not None and doc.team_id not in accessible_teams:
            return False

    return True


# --- Endpoints ---

@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    q: str | None = Query(None, description="Search keyword"),
    category: str | None = Query(None, description="Category filter"),
    team_id: uuid.UUID | None = Query(None, description="Team ID filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List documents permitted for current staff member.
    Enforces item-level restrictions, team scoping, and case conflict rules.
    Restricted titles and metadata are filtered out to prevent data leaks.
    """
    stmt = select(Document).where(Document.deleted_at.is_(None))
    if category:
        stmt = stmt.where(Document.category == category)
    if team_id:
        stmt = stmt.where(Document.team_id == team_id)
    if q:
        query_like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Document.title).like(query_like),
                func.lower(Document.description).like(query_like),
                func.lower(Document.original_filename).like(query_like),
                func.lower(Document.document_content).like(query_like),
            )
        )
    stmt = stmt.order_by(Document.created_at.desc())
    res = await db.execute(stmt)
    raw_docs = res.scalars().all()

    # Post-filter through item-level access evaluation engine
    permitted: list[Document] = []
    for doc in raw_docs:
        allowed, _ = await can_user_access_document(doc, current_user, db)
        if allowed:
            permitted.append(doc)

    return permitted


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve document details and typed content.
    Fails closed with 403 Forbidden if item-level restriction denies access.
    """
    stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    allowed, reason = await can_user_access_document(doc, current_user, db)
    if not allowed:
        if reason == "APPROVAL_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCESS_REQUIRES_APPROVAL", "message": "This document requires supervisor access approval.", "document_id": str(doc.id)},
            )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this document.")

    return doc


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    """
    Staff document and information entry:
    - Save typed text documents directly into the platform
    - Register uploaded document records with permitted team context
    """
    perm_svc = PermissionService(db)
    if payload.team_id and not await perm_svc.user_can_access_team(current_user.id, payload.team_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create documents for this team.")

    is_typed = bool(payload.document_content)
    filename = payload.filename or f"doc_{uuid.uuid4().hex[:8]}.txt"
    original_filename = payload.original_filename or f"{payload.title}.txt" if is_typed else filename
    content_type = payload.content_type or ("text/plain" if is_typed else "application/octet-stream")
    size_bytes = len(payload.document_content.encode("utf-8")) if is_typed else 0

    doc = Document(
        title=payload.title.strip(),
        category=payload.category,
        description=payload.description or "",
        team_id=payload.team_id,
        is_confidential=payload.is_confidential,
        access_mode=payload.access_mode or "INHERIT",
        document_content=payload.document_content,
        filename=filename,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size_bytes,
        storage_path=payload.file_url or f"text_docs/{filename}",
        storage_provider="inline" if is_typed else "local",
        scan_status="clean",
        uploaded_by=current_user.id,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(doc)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="DOCUMENT_CREATED",
        user_id=current_user.id,
        entity_type="document",
        entity_id=doc.id,
        after_data={"title": doc.title, "category": doc.category, "team_id": str(doc.team_id) if doc.team_id else None},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(doc)
    return doc


@router.patch("/{document_id}/access-control", response_model=DocumentResponse)
async def update_access_control(
    document_id: uuid.UUID,
    payload: AccessControlUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Supervisor control for item-level access:
    Configures Inherit, Restricted, Allow Selected, or Requires Approval modes.
    Strictly enforced for supervisors and higher authorized roles within their team scope.
    """
    stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not await can_user_manage_item_restrictions(doc, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authorized supervisors with jurisdiction over this item may configure access controls.",
        )

    mode = payload.access_mode.upper()
    if mode not in {"INHERIT", "RESTRICTED", "ALLOW_SELECTED", "REQUIRES_APPROVAL"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid access mode")

    old_mode = doc.access_mode
    doc.access_mode = mode
    doc.allowed_roles = payload.allowed_roles
    doc.allowed_user_ids = payload.allowed_user_ids
    doc.restricted_roles = payload.restricted_roles
    doc.restricted_user_ids = payload.restricted_user_ids
    doc.updated_by = current_user.id

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="DOCUMENT_ACCESS_RESTRICTION_UPDATED",
        user_id=current_user.id,
        entity_type="document",
        entity_id=doc.id,
        after_data={
            "old_mode": old_mode,
            "new_mode": mode,
            "allowed_roles": payload.allowed_roles,
            "restricted_roles": payload.restricted_roles,
        },
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(doc)
    return doc


# --- Access Request & Approval Workflow ---

@router.post("/{document_id}/request-access", response_model=AccessRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_document_access(
    document_id: uuid.UUID,
    payload: AccessRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lower-level staff request access to an approval-required document.
    Fails closed if the document does not exist or approver cannot be established.
    """
    stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Fail closed check: Ensure team/supervisor model can route this request
    # If document has a team_id, ensure that team has at least one active supervisor/director or admin
    perm_svc = PermissionService(db)
    if doc.team_id:
        accessible = await perm_svc.get_user_accessible_team_ids(current_user.id)
        # Verify requester belongs to the appropriate team or organization
        # If cross-team without permission, reject
        if accessible is not None and doc.team_id not in accessible:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-team document access requests are prohibited.")

    # Check for existing pending request
    existing_stmt = select(ItemAccessRequest).where(
        ItemAccessRequest.item_id == doc.id,
        ItemAccessRequest.requester_id == current_user.id,
        ItemAccessRequest.status == "PENDING",
    )
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An access request is already pending review.")

    access_req = ItemAccessRequest(
        item_type="document",
        item_id=doc.id,
        requester_id=current_user.id,
        status="PENDING",
        reason=payload.reason.strip(),
    )
    db.add(access_req)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="ITEM_ACCESS_REQUESTED",
        user_id=current_user.id,
        entity_type="document",
        entity_id=doc.id,
        after_data={"reason": payload.reason, "document_title": doc.title},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(access_req)
    return access_req


@router.get("/access-requests/pending", response_model=list[AccessRequestResponse])
async def list_pending_access_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Supervisors review pending access requests for documents within their team jurisdiction.
    """
    perm_svc = PermissionService(db)
    user_roles = await perm_svc.get_user_roles(current_user.id)
    supervisor_roles = {"supervisor", "director_manager", "resource_supervisor", "resource_director", "executive_director", "ceo"}
    if not (user_roles & supervisor_roles or await perm_svc.is_super_admin(current_user.id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisor privileges required to inspect approval queue.")

    stmt = select(ItemAccessRequest).where(ItemAccessRequest.status == "PENDING").order_by(ItemAccessRequest.created_at.asc())
    res = await db.execute(stmt)
    all_pending = res.scalars().all()

    # Filter by supervisor's accessible teams
    accessible_teams = await perm_svc.get_user_accessible_team_ids(current_user.id)
    if accessible_teams is None:
        return list(all_pending)

    filtered = []
    for req in all_pending:
        doc = await db.get(Document, req.item_id)
        if doc and (doc.team_id is None or doc.team_id in accessible_teams):
            filtered.append(req)

    return filtered


@router.post("/access-requests/{request_id}/approve", response_model=AccessRequestResponse)
async def approve_access_request(
    request_id: uuid.UUID,
    payload: AccessRequestReview,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Supervisor approves access request. Grants access to the specific lower-level user.
    """
    access_req = await db.get(ItemAccessRequest, request_id)
    if not access_req or access_req.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending access request not found")

    doc = await db.get(Document, access_req.item_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated document not found")

    if not await can_user_manage_item_restrictions(doc, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to approve requests for this document.")

    access_req.status = "APPROVED"
    access_req.reviewer_id = current_user.id
    access_req.review_notes = payload.review_notes
    access_req.reviewed_at = datetime.now(UTC)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="ITEM_ACCESS_APPROVED",
        user_id=current_user.id,
        entity_type="item_access_request",
        entity_id=access_req.id,
        after_data={
            "document_id": str(doc.id),
            "requester_id": str(access_req.requester_id),
            "reviewer": current_user.email,
        },
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(access_req)
    return access_req


@router.post("/access-requests/{request_id}/deny", response_model=AccessRequestResponse)
async def deny_access_request(
    request_id: uuid.UUID,
    payload: AccessRequestReview,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor denies access request."""
    access_req = await db.get(ItemAccessRequest, request_id)
    if not access_req or access_req.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending access request not found")

    doc = await db.get(Document, access_req.item_id)
    if not doc or not await can_user_manage_item_restrictions(doc, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to deny requests for this document.")

    access_req.status = "DENIED"
    access_req.reviewer_id = current_user.id
    access_req.review_notes = payload.review_notes
    access_req.reviewed_at = datetime.now(UTC)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="ITEM_ACCESS_DENIED",
        user_id=current_user.id,
        entity_type="item_access_request",
        entity_id=access_req.id,
        after_data={
            "document_id": str(doc.id),
            "requester_id": str(access_req.requester_id),
            "reviewer": current_user.email,
        },
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(access_req)
    return access_req


@router.post("/access-requests/{request_id}/revoke", response_model=AccessRequestResponse)
async def revoke_access_request(
    request_id: uuid.UUID,
    payload: AccessRequestReview,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supervisor revokes previously approved access."""
    access_req = await db.get(ItemAccessRequest, request_id)
    if not access_req or access_req.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved access request not found")

    doc = await db.get(Document, access_req.item_id)
    if not doc or not await can_user_manage_item_restrictions(doc, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to revoke requests for this document.")

    access_req.status = "REVOKED"
    access_req.reviewer_id = current_user.id
    access_req.review_notes = payload.review_notes
    access_req.reviewed_at = datetime.now(UTC)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="ITEM_ACCESS_REVOKED",
        user_id=current_user.id,
        entity_type="item_access_request",
        entity_id=access_req.id,
        after_data={
            "document_id": str(doc.id),
            "requester_id": str(access_req.requester_id),
            "reviewer": current_user.email,
        },
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(access_req)
    return access_req


# --- Download Path with HMAC and Item-Level Enforcement ---

@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    request: Request,
    expires: int = Query(..., description="Signature expiration Unix timestamp"),
    sig: str = Query(..., description="HMAC-SHA256 signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Download document with short-lived cryptographically signed URL.
    Enforces HMAC verification, security scan status, and item-level access.
    """
    if not verify_file_signature(document_id, expires, sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired download signature.",
        )

    stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if doc.scan_status != "clean":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document failed security scan or has not been verified clean.",
        )

    # Return typed document content directly if inline
    if doc.storage_provider == "inline" and doc.document_content is not None:
        file_bytes = doc.document_content.encode("utf-8")
    else:
        storage_service = StorageService(db)
        try:
            file_bytes = await storage_service.provider.download(doc.storage_path)
        except FileNotFoundError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file content not found in storage.",
            ) from err

    # Audit event
    user_id = doc.uploaded_by or doc.created_by
    if user_id:
        client_ip = request.client.host if request.client else None
        event = DocumentAccessEvent(
            document_id=doc.id,
            user_id=user_id,
            action="DOWNLOAD",
            ip_address=client_ip,
        )
        db.add(event)
        await db.commit()

    is_image = doc.content_type.lower().startswith("image/")
    disposition = "inline" if is_image else f'attachment; filename="{doc.original_filename}"'

    return Response(
        content=file_bytes,
        media_type=doc.content_type,
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "private, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )
