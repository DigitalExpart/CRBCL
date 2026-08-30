"""Pytest configuration and fixtures for CRBCL backend tests."""

import os
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

# Set test environment
os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SESSION_SECRET"] = "test-secret-key-at-least-32-chars-long-here-12345"

# Register SQLite compilation handlers for PostgreSQL types
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"

from app.auth.security import create_access_token, hash_password
from app.core.database import Base, get_db
from app.main import create_app
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.permissions.constants import Permissions

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_database():
    """Create all tables in memory before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Yield an active async test database session."""
    async with test_session_factory() as session:
        yield session


@pytest.fixture
def app(db_session):
    """FastAPI test app with get_db overridden to use test session."""
    test_app = create_app()

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.fixture
async def client(app):
    """Async HTTP client for testing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def seed_roles_and_permissions(db_session: AsyncSession):
    """Seed baseline permissions and roles into the test database."""
    # Create Permissions
    perms = {}
    for p_key in [
        # Phase 3 Intake Permissions
        Permissions.INTAKE_READ, Permissions.INTAKE_CREATE, Permissions.INTAKE_UPDATE,
        Permissions.INTAKE_DELETE, Permissions.INTAKE_ASSIGN, Permissions.INTAKE_SUBMIT,
        Permissions.INTAKE_APPROVE, Permissions.INTAKE_RETURN,
        Permissions.INTAKE_REPORTER_READ, Permissions.INTAKE_REPORTER_WRITE,
        Permissions.INTAKE_DECISION_READ, Permissions.INTAKE_DECISION_WRITE,
        Permissions.INTAKE_HISTORY_READ, Permissions.INTAKE_LINK_READ, Permissions.INTAKE_LINK_WRITE,
        # Phase 1 & 2 Permissions
        Permissions.CLIENT_READ, Permissions.CLIENT_CREATE, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_IDENTIFIERS_READ, Permissions.CLIENT_IDENTIFIERS_WRITE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_MEDICAL_WRITE,
        Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_SCHOOL_WRITE,
        Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_CULTURAL_WRITE,
        Permissions.FAMILY_READ, Permissions.FAMILY_CREATE, Permissions.FAMILY_UPDATE,
        Permissions.FAMILY_RELATIONSHIPS_READ, Permissions.FAMILY_RELATIONSHIPS_WRITE,
        Permissions.HOUSEHOLD_READ, Permissions.HOUSEHOLD_WRITE,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.SCHOOL_READ, Permissions.SCHOOL_WRITE,
        Permissions.CASE_READ, Permissions.CASE_CREATE, Permissions.CASE_UPDATE,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE,
        Permissions.ADMIN_USERS_MANAGE, Permissions.ADMIN_ROLES_MANAGE,
        Permissions.ADMIN_TEAMS_MANAGE, Permissions.ADMIN_CONFIGURATION_MANAGE,
        Permissions.AUDIT_READ,
        Permissions.TIMELINE_READ,
    ]:
        p = Permission(key=p_key, name=p_key, category="test")
        db_session.add(p)
        perms[p_key] = p
    await db_session.flush()

    # Create Caseworker Role
    caseworker_role = Role(key="caseworker", name="Caseworker", is_system=True)
    db_session.add(caseworker_role)

    # Create Supervisor Role
    supervisor_role = Role(key="supervisor", name="Supervisor", is_system=True)
    db_session.add(supervisor_role)

    # Create IT Admin Role (NO clinical/client/intake permissions!)
    it_admin_role = Role(key="it_admin", name="IT Admin", is_system=True)
    db_session.add(it_admin_role)
    await db_session.flush()

    # Grant Caseworker permissions
    for p_key in [
        Permissions.INTAKE_READ, Permissions.INTAKE_CREATE, Permissions.INTAKE_UPDATE,
        Permissions.INTAKE_SUBMIT,
        Permissions.INTAKE_REPORTER_READ, Permissions.INTAKE_REPORTER_WRITE,
        Permissions.INTAKE_DECISION_READ, Permissions.INTAKE_DECISION_WRITE,
        Permissions.INTAKE_HISTORY_READ, Permissions.INTAKE_LINK_READ, Permissions.INTAKE_LINK_WRITE,
        Permissions.CLIENT_READ, Permissions.CLIENT_CREATE, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_IDENTIFIERS_READ, Permissions.CLIENT_IDENTIFIERS_WRITE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_MEDICAL_WRITE,
        Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_SCHOOL_WRITE,
        Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_CULTURAL_WRITE,
        Permissions.FAMILY_READ, Permissions.FAMILY_CREATE, Permissions.FAMILY_UPDATE,
        Permissions.FAMILY_RELATIONSHIPS_READ, Permissions.FAMILY_RELATIONSHIPS_WRITE,
        Permissions.HOUSEHOLD_READ, Permissions.HOUSEHOLD_WRITE,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.SCHOOL_READ, Permissions.SCHOOL_WRITE,
        Permissions.CASE_READ, Permissions.CASE_CREATE, Permissions.CASE_UPDATE,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE,
        Permissions.TIMELINE_READ,
    ]:
        rp = RolePermission(role_id=caseworker_role.id, permission_id=perms[p_key].id)
        db_session.add(rp)

    # Grant Supervisor permissions (including intake approval & return)
    for p_key in [
        Permissions.INTAKE_READ, Permissions.INTAKE_CREATE, Permissions.INTAKE_UPDATE,
        Permissions.INTAKE_ASSIGN, Permissions.INTAKE_SUBMIT, Permissions.INTAKE_APPROVE, Permissions.INTAKE_RETURN,
        Permissions.INTAKE_REPORTER_READ, Permissions.INTAKE_REPORTER_WRITE,
        Permissions.INTAKE_DECISION_READ, Permissions.INTAKE_DECISION_WRITE,
        Permissions.INTAKE_HISTORY_READ, Permissions.INTAKE_LINK_READ, Permissions.INTAKE_LINK_WRITE,
        Permissions.CLIENT_READ, Permissions.CLIENT_CREATE, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_IDENTIFIERS_READ, Permissions.CLIENT_IDENTIFIERS_WRITE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_MEDICAL_WRITE,
        Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_SCHOOL_WRITE,
        Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_CULTURAL_WRITE,
        Permissions.FAMILY_READ, Permissions.FAMILY_CREATE, Permissions.FAMILY_UPDATE,
        Permissions.FAMILY_RELATIONSHIPS_READ, Permissions.FAMILY_RELATIONSHIPS_WRITE,
        Permissions.HOUSEHOLD_READ, Permissions.HOUSEHOLD_WRITE,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.SCHOOL_READ, Permissions.SCHOOL_WRITE,
        Permissions.CASE_READ, Permissions.CASE_CREATE, Permissions.CASE_UPDATE,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE,
        Permissions.TIMELINE_READ,
    ]:
        rp = RolePermission(role_id=supervisor_role.id, permission_id=perms[p_key].id)
        db_session.add(rp)

    # IT Admin gets ONLY system admin
    for p_key in [
        Permissions.ADMIN_USERS_MANAGE, Permissions.ADMIN_ROLES_MANAGE,
        Permissions.ADMIN_TEAMS_MANAGE, Permissions.ADMIN_CONFIGURATION_MANAGE,
        Permissions.AUDIT_READ,
    ]:
        rp = RolePermission(role_id=it_admin_role.id, permission_id=perms[p_key].id)
        db_session.add(rp)

    # Create a Test Team
    team = Team(code="cfs_protection", name="Child & Family Services (Protection)", short_name="CFS")
    db_session.add(team)

    await db_session.commit()
    return {
        "roles": {
            "caseworker": caseworker_role,
            "supervisor": supervisor_role,
            "it_admin": it_admin_role,
        },
        "team": team,
    }


@pytest.fixture
async def caseworker_user(db_session: AsyncSession, seed_roles_and_permissions):
    """Create an active caseworker user with token."""
    user = User(
        email="worker@crbcl.ca",
        email_normalized="worker@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Sarah Caseworker",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(user_id=user.id, role_id=seed_roles_and_permissions["roles"]["caseworker"].id)
    db_session.add(ur)

    tm = TeamMembership(user_id=user.id, team_id=seed_roles_and_permissions["team"].id, is_primary=True)
    db_session.add(tm)

    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def supervisor_user(db_session: AsyncSession, seed_roles_and_permissions):
    """Create an active supervisor user with token."""
    user = User(
        email="supervisor@crbcl.ca",
        email_normalized="supervisor@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="Karen Supervisor",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(user_id=user.id, role_id=seed_roles_and_permissions["roles"]["supervisor"].id)
    db_session.add(ur)

    tm = TeamMembership(user_id=user.id, team_id=seed_roles_and_permissions["team"].id, is_primary=True)
    db_session.add(tm)

    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def it_admin_user(db_session: AsyncSession, seed_roles_and_permissions):
    """Create an active IT Admin user."""
    user = User(
        email="itadmin@crbcl.ca",
        email_normalized="itadmin@crbcl.ca",
        password_hash=hash_password("password123"),
        full_name="IT Administrator",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(user_id=user.id, role_id=seed_roles_and_permissions["roles"]["it_admin"].id)
    db_session.add(ur)
    await db_session.commit()

    token = create_access_token(user.id)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
