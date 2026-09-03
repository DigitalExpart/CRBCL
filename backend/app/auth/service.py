"""Authentication service — login, logout, refresh, registration with safe backoff lockout."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import get_settings
from app.models.role import Role, UserRole
from app.models.user import Session, User


def _calculate_lockout_duration(failed_attempts: int) -> timedelta | None:
    """
    Exponential backoff lockout tiers:
    - 5 to 6 failed attempts: 1 minute temporary backoff
    - 7 to 9 failed attempts: 5 minutes temporary backoff
    - 10 to 14 failed attempts: 15 minutes temporary backoff
    - 15+ failed attempts: 30 minutes temporary backoff
    Prevents trivial DoS attacks while protecting against brute force.
    """
    if failed_attempts >= 15:
        return timedelta(minutes=30)
    elif failed_attempts >= 10:
        return timedelta(minutes=15)
    elif failed_attempts >= 7:
        return timedelta(minutes=5)
    elif failed_attempts >= 5:
        return timedelta(minutes=1)
    return None


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, email: str, password: str) -> User | None:
        """Verify email/password and return user if valid."""
        normalized = email.strip().lower()
        result = await self.db.execute(select(User).where(User.email_normalized == normalized))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Check temporary lockout backoff
        now = datetime.now(UTC)
        if user.locked_until and user.locked_until > now:
            return None

        if not verify_password(password, user.password_hash):
            user.failed_login_count += 1
            lockout_duration = _calculate_lockout_duration(user.failed_login_count)
            if lockout_duration:
                user.locked_until = now + lockout_duration
            await self.db.flush()
            return None

        # Reset failed attempts on successful authentication
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = now
        await self.db.flush()
        return user

    async def unlock_user(self, user_id: uuid.UUID) -> bool:
        """Administrative unlock for locked accounts."""
        user = await self.get_user_by_id(user_id)
        if user:
            user.failed_login_count = 0
            user.locked_until = None
            await self.db.flush()
            return True
        return False

    async def create_session(
        self, user: User, user_agent: str | None = None, ip_address: str | None = None
    ) -> tuple[str, str]:
        """Create access + refresh tokens and persist session."""
        settings = get_settings()

        # Collect user permissions for token
        permissions = self._get_user_permissions(user)
        roles = [ur.role.key for ur in user.roles if ur.role and ur.role.is_active]

        access_token = create_access_token(
            user.id,
            extra={"roles": roles, "permissions": permissions},
        )
        refresh_token = create_refresh_token()

        session = Session(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl),
        )
        self.db.add(session)
        await self.db.flush()
        return access_token, refresh_token

    async def refresh_session(self, refresh_token: str) -> tuple[str, str] | None:
        """Validate refresh token and issue new access + refresh tokens."""
        token_hash = hash_refresh_token(refresh_token)
        result = await self.db.execute(
            select(Session).where(
                Session.refresh_token_hash == token_hash,
                Session.is_revoked == False,  # noqa: E712
                Session.expires_at > datetime.now(UTC),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return None

        # Load user
        user_result = await self.db.execute(select(User).where(User.id == session.user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active or user.is_deleted:
            return None

        # Revoke old session
        session.is_revoked = True
        session.revoked_at = datetime.now(UTC)

        # Create new session
        return await self.create_session(user, session.user_agent, session.ip_address)

    async def revoke_session(self, refresh_token: str) -> bool:
        """Revoke a specific refresh token / session."""
        token_hash = hash_refresh_token(refresh_token)
        result = await self.db.execute(select(Session).where(Session.refresh_token_hash == token_hash))
        session = result.scalar_one_or_none()
        if session:
            session.is_revoked = True
            session.revoked_at = datetime.now(UTC)
            await self.db.flush()
            return True
        return False

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """Revoke all active sessions for a user."""
        result = await self.db.execute(
            select(Session).where(Session.user_id == user_id, Session.is_revoked == False)  # noqa: E712
        )
        sessions = result.scalars().all()
        now = datetime.now(UTC)
        for s in sessions:
            s.is_revoked = True
            s.revoked_at = now
        await self.db.flush()
        return len(sessions)

    async def register_user(self, email: str, password: str, full_name: str = "", default_role_key: str = "caseworker") -> User:
        """Create a new user account and assign default role."""
        normalized = email.strip().lower()
        user = User(
            email=email.strip(),
            email_normalized=normalized,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Assign default caseworker role
        role_res = await self.db.execute(select(Role).where(Role.key == default_role_key, Role.is_active == True))
        role = role_res.scalar_one_or_none()
        if not role:
            fallback_res = await self.db.execute(select(Role).where(Role.is_active == True).limit(1))
            role = fallback_res.scalar_one_or_none()

        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            self.db.add(user_role)
            await self.db.flush()

        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        result = await self.db.execute(select(User).where(User.email_normalized == normalized))
        return result.scalar_one_or_none()

    @staticmethod
    def _get_user_permissions(user: User) -> list[str]:
        """Collect all permission keys from user's active roles."""
        permissions = set()
        for user_role in user.roles:
            role = user_role.role
            if not role or not role.is_active:
                continue
            for rp in role.permissions:
                if rp.permission and rp.permission.is_active:
                    permissions.add(rp.permission.key)
        return sorted(permissions)
