"""Targeted tests for Post Majority staff roles, registration, and admin user creation."""

import pytest
from sqlalchemy import select

from app.auth.security import create_access_token, hash_password
from app.models.role import Role, UserRole
from app.models.user import User


@pytest.fixture
async def setup_post_majority_test_data(db_session, seed_roles_and_permissions):
    """Ensure admin user exists with admin permissions."""
    admin_user = User(
        email="admin@crbcl.ca",
        email_normalized="admin@crbcl.ca",
        full_name="IT Admin",
        display_name="IT Admin",
        department="IT & Systems",
        password_hash=hash_password("Admin@CRBCL2026!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin_user)
    await db_session.flush()

    it_res = await db_session.execute(select(Role).where(Role.key == "it_admin"))
    it_role = it_res.scalar_one()
    db_session.add(UserRole(user_id=admin_user.id, role_id=it_role.id))
    await db_session.commit()
    return admin_user


@pytest.mark.asyncio
async def test_registration_with_post_majority_roles(client, setup_post_majority_test_data):
    """Verify that all 5 Post Majority roles are selectable and valid during registration."""
    test_cases = [
        ("pm.mentor@test.com", "mentor"),
        ("pm.casework@test.com", "casework"),
        ("pm.caseworker@test.com", "caseworker"),
        ("pm.adminassistant@test.com", "admin_assistant"),
        ("pm.supervisor@test.com", "supervisor"),
        ("pm.director@test.com", "director"),
        ("pm.director_mgr@test.com", "director_manager"),
    ]

    for email, requested_role in test_cases:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "SecurePassword123!",
                "full_name": f"Test {requested_role}",
                "department": "Post-Majority (Young Adults)",
                "requested_role": requested_role,
            },
        )
        assert resp.status_code == 200, f"Registration failed for role {requested_role}: {resp.text}"
        data = resp.json()
        assert data["email"] == email


@pytest.mark.asyncio
async def test_admin_create_post_majority_staff_accounts(client, setup_post_majority_test_data, db_session):
    """Verify admin creation of active Post Majority staff accounts with roles and teams."""
    admin_user = setup_post_majority_test_data
    token = create_access_token(admin_user.id, extra={"email": admin_user.email, "role": "it_admin"})
    headers = {"Authorization": f"Bearer {token}"}

    staff_roles_to_create = [
        ("Trevor Mentor", "trevor.mentor@redbearlodge.ca", "mentor"),
        ("Dean Casework", "dean.casework@redbearlodge.ca", "casework"),
        ("Denise AdminAssistant", "denise.assistant@redbearlodge.ca", "admin_assistant"),
        ("Tracy Supervisor", "tracy.supervisor@redbearlodge.ca", "supervisor"),
        ("Tobi Director", "tobi.director@redbearlodge.ca", "director"),
    ]

    for name, email, role_key in staff_roles_to_create:
        resp = await client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "full_name": name,
                "email": email,
                "password": "TemporaryPassword2026!",
                "department": "Post-Majority (Young Adults)",
                "role_keys": [role_key],
                "team_access": ["22"],
            },
        )
        assert resp.status_code == 201, f"Failed to create user with role {role_key}: {resp.text}"
        data = resp.json()
        assert data["is_active"] is True
        assert data["is_verified"] is True
        assert data["department"] == "Post-Majority (Young Adults)"
        expected_role = "caseworker" if role_key == "casework" else ("director_manager" if role_key == "director" else role_key)
        assert expected_role in data["roles"], f"Expected {expected_role} in roles {data['roles']}"


@pytest.mark.asyncio
async def test_post_majority_staff_seeded_in_baseline():
    """Verify that the 5 Post Majority staff are defined in baseline staff data."""
    from app.core.permission_sync import BASELINE_STAFF_DATA
    pm_emails = {
        "tobi.heavyrunner@redbearlodge.ca": "director_manager",
        "tracy.delorme@redbearlodge.ca": "supervisor",
        "dean.sparvier@redbearlodge.ca": "caseworker",
        "trevor.desjarlais@redbearlodge.ca": "mentor",
        "denise.pelletier@redbearlodge.ca": "admin_assistant",
    }
    baseline_map = {s["email"].lower(): s for s in BASELINE_STAFF_DATA}
    for email, expected_role in pm_emails.items():
        assert email.lower() in baseline_map, f"Missing staff {email} in baseline"
        staff = baseline_map[email.lower()]
        assert expected_role in staff["roles"], f"Expected role {expected_role} for {email}, got {staff['roles']}"
        assert staff.get("department") == "Post-Majority (Young Adults)"

    # Verify Policy and Data staff
    policy_emails = {
        "angela.yellowbird@redbearlodge.ca": "policy_manager",
        "thomas.favel@redbearlodge.ca": "policy_analyst",
    }
    for p_email, p_role in policy_emails.items():
        assert p_email.lower() in baseline_map, f"Missing policy staff {p_email} in baseline"
        p_staff = baseline_map[p_email.lower()]
        assert p_role in p_staff["roles"], f"Expected role {p_role} for {p_email}, got {p_staff['roles']}"
        assert p_staff.get("department") == "Policy & Data"
