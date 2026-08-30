"""User repository."""

from __future__ import annotations

import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role, UserRole
from app.models.team import TeamMembership, UserTeamAccess
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_with_roles_and_teams(self, user_id: uuid.UUID) -> User | None:
        query = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        query_text: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[User], int]:
        query = (
            select(User)
            .where(User.deleted_at.is_(None))
            .options(
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(
                User.email.ilike(search_pattern) | User.full_name.ilike(search_pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def assign_roles(self, user_id: uuid.UUID, role_keys: list[str], assigned_by: uuid.UUID | None = None) -> None:
        """Replace user roles with new list of role keys."""
        # Find role models
        roles_res = await self.db.execute(select(Role).where(Role.key.in_(role_keys)))
        roles = list(roles_res.scalars().all())

        # Clear existing
        existing_res = await self.db.execute(select(UserRole).where(UserRole.user_id == user_id))
        for ur in existing_res.scalars().all():
            await self.db.delete(ur)

        # Add new
        for role in roles:
            ur = UserRole(user_id=user_id, role_id=role.id, assigned_by=assigned_by)
            self.db.add(ur)
        await self.db.flush()

    async def assign_teams(self, user_id: uuid.UUID, team_ids: list[uuid.UUID], assigned_by: uuid.UUID | None = None) -> None:
        """Replace user team memberships."""
        existing_res = await self.db.execute(select(TeamMembership).where(TeamMembership.user_id == user_id))
        for tm in existing_res.scalars().all():
            await self.db.delete(tm)

        for i, team_id in enumerate(team_ids):
            tm = TeamMembership(
                user_id=user_id,
                team_id=team_id,
                is_primary=(i == 0),
                is_active=True,
            )
            self.db.add(tm)
        await self.db.flush()
