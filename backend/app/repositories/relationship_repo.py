"""Family membership and directional relationships repository."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.relationship import FamilyMember, FamilyRelationship


class RelationshipRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_family_members(self, family_id: uuid.UUID) -> list[FamilyMember]:
        query = (
            select(FamilyMember)
            .where(FamilyMember.family_id == family_id, FamilyMember.is_active == True)  # noqa: E712
            .options(selectinload(FamilyMember.person))
            .order_by(FamilyMember.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_family_member(
        self, family_id: uuid.UUID, person_id: uuid.UUID, role: str = "Member", notes: str = ""
    ) -> FamilyMember:
        member = FamilyMember(
            family_id=family_id,
            person_id=person_id,
            role=role,
            is_active=True,
            notes=notes,
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def list_family_relationships(
        self, family_id: uuid.UUID | None = None, person_id: uuid.UUID | None = None
    ) -> list[FamilyRelationship]:
        query = (
            select(FamilyRelationship)
            .where(FamilyRelationship.is_active == True)  # noqa: E712
            .options(
                selectinload(FamilyRelationship.person_a),
                selectinload(FamilyRelationship.person_b),
            )
        )

        if family_id:
            query = query.where(FamilyRelationship.family_id == family_id)

        if person_id:
            query = query.where(
                or_(
                    FamilyRelationship.person_a_id == person_id,
                    FamilyRelationship.person_b_id == person_id,
                )
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_relationship(
        self,
        person_a_id: uuid.UUID,
        person_b_id: uuid.UUID,
        relationship_type: str,
        family_id: uuid.UUID | None = None,
        notes: str = "",
    ) -> FamilyRelationship:
        rel = FamilyRelationship(
            family_id=family_id,
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            relationship_type=relationship_type,
            is_active=True,
            notes=notes,
        )
        self.db.add(rel)
        await self.db.flush()
        return rel
