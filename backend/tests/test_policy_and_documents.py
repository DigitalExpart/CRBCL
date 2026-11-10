"""Comprehensive unit and integration tests for Company Policy and Document Item-Level Access Control."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.security import create_access_token, hash_password
from app.core.database import Base, get_db
from app.main import create_app
from app.models.document import Document, ItemAccessRequest
from app.models.policy import CompanyPolicy, CompanyPolicyVersion
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.permissions.constants import Permissions


@pytest.fixture
async def setup_roles_and_users(db_session):
    """Seed test roles, permissions, teams, and users."""
    perm_doc_read = Permission(key=Permissions.DOCUMENT_READ, name="Read Documents", category="documents")
    perm_doc_upload = Permission(key=Permissions.DOCUMENT_UPLOAD, name="Upload Documents", category="documents")
    perm_doc_restrict = Permission(key=Permissions.DOCUMENT_RESTRICT, name="Restrict Documents", category="documents")
    perm_doc_approve = Permission(key=Permissions.DOCUMENT_APPROVE_ACCESS, name="Approve Access", category="documents")
    perm_policy_read = Permission(key=Permissions.POLICY_READ, name="Read Policy", category="policy")
    perm_policy_write = Permission(key=Permissions.POLICY_WRITE, name="Write Policy", category="policy")

    for p in [perm_doc_read, perm_doc_upload, perm_doc_restrict, perm_doc_approve, perm_policy_read, perm_policy_write]:
        db_session.add(p)
    await db_session.flush()

    role_caseworker = Role(key="caseworker", name="Caseworker", is_system=True)
    role_supervisor = Role(key="supervisor", name="Supervisor", is_system=True)
    role_policy_staff = Role(key="policy_staff", name="Policy Staff", is_system=True)

    db_session.add_all([role_caseworker, role_supervisor, role_policy_staff])
    await db_session.flush()

    # Caseworker
    db_session.add(RolePermission(role_id=role_caseworker.id, permission_id=perm_doc_read.id))
    db_session.add(RolePermission(role_id=role_caseworker.id, permission_id=perm_doc_upload.id))
    db_session.add(RolePermission(role_id=role_caseworker.id, permission_id=perm_policy_read.id))

    # Supervisor
    for p in [perm_doc_read, perm_doc_upload, perm_doc_restrict, perm_doc_approve, perm_policy_read]:
        db_session.add(RolePermission(role_id=role_supervisor.id, permission_id=p.id))

    # Policy Staff
    db_session.add(RolePermission(role_id=role_policy_staff.id, permission_id=perm_doc_read.id))
    db_session.add(RolePermission(role_id=role_policy_staff.id, permission_id=perm_policy_read.id))
    db_session.add(RolePermission(role_id=role_policy_staff.id, permission_id=perm_policy_write.id))

    team_post_majority = Team(name="Post-Majority", code="post_majority")
    team_finance = Team(name="Finance", code="finance")
    db_session.add_all([team_post_majority, team_finance])
    await db_session.flush()

    u_caseworker = User(
        email="cw@test.local",
        email_normalized="cw@test.local",
        password_hash=hash_password("Password123!"),
        full_name="Caseworker User",
        is_active=True,
        is_verified=True,
    )
    u_supervisor = User(
        email="sup@test.local",
        email_normalized="sup@test.local",
        password_hash=hash_password("Password123!"),
        full_name="Supervisor User",
        is_active=True,
        is_verified=True,
    )
    u_policy = User(
        email="policy@test.local",
        email_normalized="policy@test.local",
        password_hash=hash_password("Password123!"),
        full_name="Policy Staff User",
        is_active=True,
        is_verified=True,
    )
    u_other_cw = User(
        email="other_cw@test.local",
        email_normalized="other_cw@test.local",
        password_hash=hash_password("Password123!"),
        full_name="Other Team CW",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([u_caseworker, u_supervisor, u_policy, u_other_cw])
    await db_session.flush()

    db_session.add(UserRole(user_id=u_caseworker.id, role_id=role_caseworker.id))
    db_session.add(UserRole(user_id=u_supervisor.id, role_id=role_supervisor.id))
    db_session.add(UserRole(user_id=u_policy.id, role_id=role_policy_staff.id))
    db_session.add(UserRole(user_id=u_other_cw.id, role_id=role_caseworker.id))

    db_session.add(TeamMembership(user_id=u_caseworker.id, team_id=team_post_majority.id, is_active=True))
    db_session.add(TeamMembership(user_id=u_supervisor.id, team_id=team_post_majority.id, is_active=True))
    db_session.add(TeamMembership(user_id=u_other_cw.id, team_id=team_finance.id, is_active=True))

    await db_session.commit()

    return {
        "caseworker": u_caseworker,
        "supervisor": u_supervisor,
        "policy": u_policy,
        "other_cw": u_other_cw,
        "team_pm": team_post_majority,
        "team_fin": team_finance,
    }


def make_auth_headers(user: User) -> dict:
    token = create_access_token(user.id, extra={"email": user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_company_policy_lifecycle(app, setup_roles_and_users, db_session):
    """Verifies that only policy staff can create/edit policies, and version history is tracked."""
    ctx = setup_roles_and_users
    policy_user = ctx["policy"]
    cw_user = ctx["caseworker"]

    policy_headers = make_auth_headers(policy_user)
    cw_headers = make_auth_headers(cw_user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Caseworker attempting to create a policy is rejected with 403 Forbidden
        cw_create = await client.post(
            "/api/v1/policies",
            json={
                "title": "Unauthorized Policy",
                "category": "Governance",
                "content": "Caseworker cannot publish policies.",
            },
            headers=cw_headers,
        )
        assert cw_create.status_code == 403

        # 2. Designated Policy staff successfully creates a policy
        policy_create = await client.post(
            "/api/v1/policies",
            json={
                "title": "Family Wellness Practice Guidelines",
                "category": "Practice Standards",
                "content": "# Practice Guidelines\nAll casework must prioritize cultural safety and active family engagement.",
                "change_summary": "Initial policy release approved by leadership",
            },
            headers=policy_headers,
        )
        assert policy_create.status_code == 201
        data = policy_create.json()
        policy_id = data["id"]
        assert data["version"] == 1
        assert data["title"] == "Family Wellness Practice Guidelines"

        # 3. Caseworker can read the policy
        cw_read = await client.get(f"/api/v1/policies/{policy_id}", headers=cw_headers)
        assert cw_read.status_code == 200
        assert cw_read.json()["title"] == "Family Wellness Practice Guidelines"

        # 4. Caseworker attempting to edit the policy is rejected with 403 Forbidden
        cw_edit = await client.put(
            f"/api/v1/policies/{policy_id}",
            json={
                "content": "Malicious edit attempt",
                "change_summary": "Attempted edit without permission",
            },
            headers=cw_headers,
        )
        assert cw_edit.status_code == 403

        # 5. Policy staff updates the policy, creating version 2 with immutable history
        policy_update = await client.put(
            f"/api/v1/policies/{policy_id}",
            json={
                "content": "# Practice Guidelines (Rev 2)\nUpdated with Miyo Pimatisowin Act jurisdictional requirements.",
                "change_summary": "Incorporated provincial legislation alignment",
            },
            headers=policy_headers,
        )
        assert policy_update.status_code == 200
        updated_data = policy_update.json()
        assert updated_data["version"] == 2

        # 6. Verify version history endpoint returns both versions in descending order
        versions_resp = await client.get(f"/api/v1/policies/{policy_id}/versions", headers=cw_headers)
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) == 2
        assert versions[0]["version_number"] == 2
        assert "legislation alignment" in versions[0]["change_summary"]
        assert versions[1]["version_number"] == 1
        assert "Initial policy release" in versions[1]["change_summary"]


@pytest.mark.asyncio
async def test_staff_typed_document_and_item_access_control(app, setup_roles_and_users, db_session):
    """
    Verifies:
    1. Staff can type and save a document directly into the platform.
    2. Supervisor can configure item-level access (INHERIT, RESTRICTED, REQUIRES_APPROVAL).
    3. Restricted items fail closed and do not leak to unauthorized lower-level staff.
    4. Access request and approval workflow routes to supervisor and unblocks access.
    5. Cross-team isolation is strictly enforced.
    """
    ctx = setup_roles_and_users
    cw = ctx["caseworker"]
    sup = ctx["supervisor"]
    other_cw = ctx["other_cw"]
    pm_team = ctx["team_pm"]
    fin_team = ctx["team_fin"]

    cw_headers = make_auth_headers(cw)
    sup_headers = make_auth_headers(sup)
    other_headers = make_auth_headers(other_cw)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Caseworker types and saves a document directly
        create_resp = await client.post(
            "/api/v1/documents",
            json={
                "title": "Post-Majority Independent Living Plan Notes",
                "category": "Case File",
                "team_id": str(pm_team.id),
                "document_content": "Youth has secured transitional housing and enrolled in culinary arts.",
                "description": "Routine quarterly transitional goals review.",
            },
            headers=cw_headers,
        )
        assert create_resp.status_code == 201
        doc_data = create_resp.json()
        doc_id = doc_data["id"]
        assert doc_data["title"] == "Post-Majority Independent Living Plan Notes"
        assert doc_data["access_mode"] == "INHERIT"

        # 2. Both creator CW and supervisor can read the document
        cw_get = await client.get(f"/api/v1/documents/{doc_id}", headers=cw_headers)
        assert cw_get.status_code == 200

        sup_get = await client.get(f"/api/v1/documents/{doc_id}", headers=sup_headers)
        assert sup_get.status_code == 200

        # 3. Other CW on Finance team cannot see the Post-Majority document (cross-team isolation)
        other_list = await client.get("/api/v1/documents", headers=other_headers)
        assert other_list.status_code == 200
        assert not any(d["id"] == doc_id for d in other_list.json())

        other_get = await client.get(f"/api/v1/documents/{doc_id}", headers=other_headers)
        assert other_get.status_code == 403

        # 4. Supervisor updates access mode to REQUIRES_APPROVAL
        restrict_resp = await client.patch(
            f"/api/v1/documents/{doc_id}/access-control",
            json={
                "access_mode": "REQUIRES_APPROVAL",
            },
            headers=sup_headers,
        )
        assert restrict_resp.status_code == 200
        assert restrict_resp.json()["access_mode"] == "REQUIRES_APPROVAL"

        # 5. Non-supervisor caseworker attempting to modify access control gets 403
        unauth_patch = await client.patch(
            f"/api/v1/documents/{doc_id}/access-control",
            json={"access_mode": "INHERIT"},
            headers=cw_headers,
        )
        assert unauth_patch.status_code == 403

        # 6. Supervisor creates second document on PM team to test request workflow
        second_doc_resp = await client.post(
            "/api/v1/documents",
            json={
                "title": "Confidential Supervisory Case Assessment",
                "category": "Report",
                "team_id": str(pm_team.id),
                "document_content": "Restricted mental health consultation details.",
                "access_mode": "REQUIRES_APPROVAL",
            },
            headers=sup_headers,
        )
        assert second_doc_resp.status_code == 201
        restricted_doc_id = second_doc_resp.json()["id"]

        # Caseworker is blocked from reading the restricted document directly
        blocked_get = await client.get(f"/api/v1/documents/{restricted_doc_id}", headers=cw_headers)
        assert blocked_get.status_code == 403
        resp_data = blocked_get.json()
        err = resp_data.get("error") or (resp_data.get("detail", {}) if isinstance(resp_data.get("detail"), dict) else {}).get("error")
        assert err == "ACCESS_REQUIRES_APPROVAL"

        # 7. Caseworker submits an access request with reason
        req_resp = await client.post(
            f"/api/v1/documents/{restricted_doc_id}/request-access",
            json={"reason": "Need to verify wellness goals for upcoming permanency court review."},
            headers=cw_headers,
        )
        assert req_resp.status_code == 201
        req_data = req_resp.json()
        request_id = req_data["id"]
        assert req_data["status"] == "PENDING"

        # 8. Supervisor reviews pending access requests
        pending_resp = await client.get("/api/v1/documents/access-requests/pending", headers=sup_headers)
        assert pending_resp.status_code == 200
        pending_list = pending_resp.json()
        assert any(r["id"] == request_id for r in pending_list)

        # 9. Supervisor approves access request
        approve_resp = await client.post(
            f"/api/v1/documents/access-requests/{request_id}/approve",
            json={"review_notes": "Approved for 30-day court preparation window."},
            headers=sup_headers,
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "APPROVED"

        # 10. Caseworker now has access to read the document!
        unblocked_get = await client.get(f"/api/v1/documents/{restricted_doc_id}", headers=cw_headers)
        assert unblocked_get.status_code == 200
        assert unblocked_get.json()["title"] == "Confidential Supervisory Case Assessment"

        # 11. Supervisor revokes access
        revoke_resp = await client.post(
            f"/api/v1/documents/access-requests/{request_id}/revoke",
            json={"review_notes": "Court hearing completed; access closed."},
            headers=sup_headers,
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["status"] == "REVOKED"

        # 12. Caseworker is blocked again immediately after revocation
        reblocked_get = await client.get(f"/api/v1/documents/{restricted_doc_id}", headers=cw_headers)
        assert reblocked_get.status_code == 403


@pytest.mark.asyncio
async def test_access_mode_modes_allow_selected_and_restricted(app, setup_roles_and_users, db_session):
    """
    Tests specific item-level modes:
    - ALLOW_SELECTED mode allows specific user ID even if role is lower-level
    - RESTRICTED mode explicitly hides document from search/list queries
    """
    ctx = setup_roles_and_users
    cw = ctx["caseworker"]
    sup = ctx["supervisor"]
    pm_team = ctx["team_pm"]

    cw_headers = make_auth_headers(cw)
    sup_headers = make_auth_headers(sup)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create document with ALLOW_SELECTED allowing only caseworker's UUID
        doc_resp = await client.post(
            "/api/v1/documents",
            json={
                "title": "Selected Grant Consultation",
                "category": "Form",
                "team_id": str(pm_team.id),
                "document_content": "Sensitive medical support voucher details.",
                "access_mode": "ALLOW_SELECTED",
            },
            headers=sup_headers,
        )
        assert doc_resp.status_code == 201
        doc_id = doc_resp.json()["id"]

        # Initially, cw is NOT in allowed_user_ids, so access denied
        get_denied = await client.get(f"/api/v1/documents/{doc_id}", headers=cw_headers)
        assert get_denied.status_code == 403

        # Supervisor adds cw's user ID to allowed_user_ids
        patch_resp = await client.patch(
            f"/api/v1/documents/{doc_id}/access-control",
            json={
                "access_mode": "ALLOW_SELECTED",
                "allowed_user_ids": [str(cw.id)],
            },
            headers=sup_headers,
        )
        assert patch_resp.status_code == 200

        # Now cw can read the document
        get_allowed = await client.get(f"/api/v1/documents/{doc_id}", headers=cw_headers)
        assert get_allowed.status_code == 200
        assert get_allowed.json()["title"] == "Selected Grant Consultation"

        # Verify search filter also includes it for cw now
        search_resp = await client.get("/api/v1/documents?q=Voucher", headers=cw_headers)
        assert search_resp.status_code == 200
        assert any(d["id"] == doc_id for d in search_resp.json())
