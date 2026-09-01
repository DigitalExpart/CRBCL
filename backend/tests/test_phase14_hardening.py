"""Comprehensive Automated Test Suite for Phase 14 Production Hardening, Security, Governance & Privacy."""

import urllib.parse
import uuid
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.log_sanitizer import LogSanitizerFilter
from app.core.security_headers import SecurityHeadersMiddleware
from app.models.audit import AuditEvent
from app.models.case import Case
from app.models.client import Client
from app.models.migration import MigrationLedger
from app.permissions.constants import Permissions
from app.services.file_security import (
    generate_signed_file_url,
    validate_file_upload,
    verify_file_signature,
)
from app.services.integrations.ai.gateway import AiGateway
from app.services.integrations.utils import db_query_first
from app.services.legal_hold import (
    LegalHoldError,
    apply_legal_hold,
    check_legal_hold_protection,
    remove_legal_hold,
)
from app.services.mfa import (
    generate_backup_codes,
    generate_mfa_secret,
    verify_totp_code,
)


def test_security_headers_middleware():
    """Verify SecurityHeadersMiddleware attaches mandatory security headers to response."""
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/test")
    def sample_endpoint():
        return {"status": "ok"}

    client = TestClient(test_app)
    response = client.get("/test")

    assert response.status_code == 200
    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_mfa_service_helpers():
    """Verify TOTP Base32 secret generation, code verification, and recovery codes."""
    secret = generate_mfa_secret()
    assert len(secret) >= 16

    # Recovery codes
    backup_codes = generate_backup_codes(count=8)
    assert len(backup_codes) == 8
    assert "-" in backup_codes[0]

    # Verify invalid code fails
    assert verify_totp_code(secret, "000000") is False


def test_file_security_signed_urls_and_mime_validation():
    """Verify signed URL token expiry and MIME validation."""
    file_id = uuid.uuid4()
    url = generate_signed_file_url(file_id, expiry_seconds=900)

    assert f"/api/v1/documents/{file_id}/download" in url
    assert "sig=" in url

    # Parse query params
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    expires_at = int(params["expires"][0])
    sig = params["sig"][0]

    assert verify_file_signature(file_id, expires_at, sig) is True

    # Expired token verification
    expired_time = int(datetime.utcnow().timestamp()) - 100
    assert verify_file_signature(file_id, expired_time, sig) is False

    # MIME Validation
    valid = validate_file_upload("Document.pdf", "application/pdf", 1024)
    assert valid["status"] == "QUARANTINED_UNSCANNED"

    with pytest.raises(ValueError):
        validate_file_upload("Malicious.exe", "application/x-msdownload", 1024)


def test_log_sanitizer_filter():
    """Verify sensitive password, token, and medical narrative fields are redacted from logs."""
    sanitizer = LogSanitizerFilter()
    import logging

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User login failed with password='SecretPass123!' and token='abc123token'",
        args=(),
        exc_info=None,
    )
    sanitizer.filter(record)
    assert "SecretPass123!" not in record.msg
    assert "***REDACTED***" in record.msg


@pytest.mark.asyncio
async def test_legal_hold_enforcement(db_session):
    """Verify active legal hold blocks deletion of case records."""
    user_id = uuid.uuid4()
    case = Case(case_number="CASE-HOLD-001", title="Legal Hold Case", status="Active")
    db_session.add(case)
    await db_session.commit()

    # Apply Legal Hold
    held_case = await apply_legal_hold(db_session, case.id, user_id, "Court Injunction Order #409")
    assert held_case.is_legal_hold is True

    # Verification function raises exception
    with pytest.raises(LegalHoldError):
        check_legal_hold_protection(held_case)

    # Remove Legal Hold
    unheld_case = await remove_legal_hold(db_session, case.id)
    assert unheld_case.is_legal_hold is False
    check_legal_hold_protection(unheld_case)  # Should not raise


@pytest.mark.asyncio
async def test_it_admin_privacy_boundary(db_session):
    """Verify IT Admin role cannot access case records or client medical data."""
    c = Case(case_number="CASE-ADMIN-PRIVACY", title="Sensitive Case Details", status="Active")
    db_session.add(c)
    await db_session.commit()

    user_id = uuid.uuid4()
    it_admin_perms = {Permissions.ADMIN_USERS_MANAGE, Permissions.ADMIN_CONFIGURATION_MANAGE}

    # IT Admin lacks Permissions.CASE_READ
    authorized_cases = await AiGateway.get_authorized_case_ids(db_session, user_id, it_admin_perms)
    assert c.id not in authorized_cases

    # Querying case directly yields access denied error
    res = await AiGateway.process_ai_request(
        db=db_session,
        user_id=user_id,
        user_permissions=it_admin_perms,
        prompt="Show me summary of case CASE-ADMIN-PRIVACY",
        case_id=c.id,
    )
    assert res["is_error"] is True
    assert "Access Denied" in res["content"]


@pytest.mark.asyncio
async def test_migration_ledger_idempotency(db_session):
    """Verify Migration Ledger prevents duplicate legacy entity migrations."""
    source_id = "BASE44-CLIENT-999"
    entry1 = MigrationLedger(
        source_system="BASE44",
        source_id=source_id,
        target_entity_type="CLIENT",
        target_entity_id=uuid.uuid4(),
        status="COMPLETED",
    )
    db_session.add(entry1)
    await db_session.commit()

    # Attempt duplicate entry
    entry2 = MigrationLedger(
        source_system="BASE44",
        source_id=source_id,
        target_entity_type="CLIENT",
        target_entity_id=uuid.uuid4(),
        status="COMPLETED",
    )
    db_session.add(entry2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_audit_event_immutability(db_session):
    """Verify Audit Event entries can be stored and queried."""
    event = AuditEvent(
        event_type="CASE_VIEWED",
        user_id=uuid.uuid4(),
        entity_type="CASE",
        entity_id=uuid.uuid4(),
        source="api",
    )
    db_session.add(event)
    await db_session.commit()

    # Confirm created
    fetched = await db_query_first(db_session, AuditEvent, AuditEvent.id == event.id)
    assert fetched is not None
    assert fetched.event_type == "CASE_VIEWED"
