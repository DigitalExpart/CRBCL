"""Test verification for CEO and Board Portal permission resolution without relying on unseeded DB join rows."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.models.role import Role, UserRole
from app.models.user import User


@pytest.fixture
async def unseeded_ceo_user(db_session: AsyncSession) -> dict:
    """CEO user whose Role has zero rows in RolePermission in the database."""
    role_res = await db_session.execute(select(Role).where(Role.key == "ceo"))
    role = role_res.scalars().first()
    if not role:
        role = Role(key="ceo", name="Chief Executive Officer", is_system=True)
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=f"geek_{uuid.uuid4().hex[:6]}@crbcl.ca",
        email_normalized=f"geek_{uuid.uuid4().hex[:6]}@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Chief Executive Officer",
        display_name="geek",
        department="Governance & Executive Leadership",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def unseeded_board_user(db_session: AsyncSession) -> dict:
    """Board member user whose Role has zero rows in RolePermission in the database."""
    role_res = await db_session.execute(select(Role).where(Role.key == "board_member"))
    role = role_res.scalars().first()
    if not role:
        role = Role(key="board_member", name="Board Member", is_system=True)
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=f"board_{uuid.uuid4().hex[:6]}@crbcl.ca",
        email_normalized=f"board_{uuid.uuid4().hex[:6]}@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Governor One",
        display_name="governor",
        department="Board of Governors",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.mark.asyncio
async def test_ceo_can_access_both_dashboards_with_unseeded_role_permissions(
    client: AsyncClient, unseeded_ceo_user: dict
):
    """CEO user with role 'ceo' successfully accesses both /ceo-dashboard and /board/summary."""
    # 1. /api/v1/auth/me returns permissions including executive and board dashboard read
    me_res = await client.get("/api/v1/auth/me", headers=unseeded_ceo_user["headers"])
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert "executive_dashboard.read" in me_data["permissions"]
    assert "board_dashboard.read" in me_data["permissions"]

    # 2. /api/v1/ceo-dashboard returns 200 OK
    ceo_res = await client.get("/api/v1/ceo-dashboard", headers=unseeded_ceo_user["headers"])
    assert ceo_res.status_code == 200
    assert "executive_summary" in ceo_res.json()

    # 3. /api/v1/board/summary returns 200 OK
    board_res = await client.get("/api/v1/board/summary", headers=unseeded_ceo_user["headers"])
    assert board_res.status_code == 200
    assert "initiatives_total" in board_res.json()


@pytest.mark.asyncio
async def test_board_member_can_access_board_but_denied_ceo_dashboard(
    client: AsyncClient, unseeded_board_user: dict
):
    """Board member user accesses /board/summary but is strictly denied /ceo-dashboard with 403."""
    # 1. /api/v1/board/summary returns 200 OK
    board_res = await client.get("/api/v1/board/summary", headers=unseeded_board_user["headers"])
    assert board_res.status_code == 200

    # 2. /api/v1/ceo-dashboard returns 403 Forbidden
    ceo_res = await client.get("/api/v1/ceo-dashboard", headers=unseeded_board_user["headers"])
    assert ceo_res.status_code == 403
    assert ceo_res.json()["error"]["code"] == "PERMISSION_DENIED"
