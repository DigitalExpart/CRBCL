"""Controlled person duplicate merge service with complete audit trail."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.client import Client
from app.models.person import Person, PersonMerge
from app.models.relationship import FamilyMember, FamilyRelationship, HouseholdMembership


class MergeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def merge_persons(
        self,
        source_person_id: uuid.UUID,
        target_person_id: uuid.UUID,
        merged_by: uuid.UUID,
        reason: str,
        notes: str = "",
    ) -> PersonMerge:
        """
        Safely merge a duplicate source person into a surviving target person.
        Re-points relationships, family memberships, households, and clients,
        soft-deletes the source person, and logs immutable audit events.
        """
        # 1. Verify existence
        src_res = await self.db.execute(select(Person).where(Person.id == source_person_id))
        source = src_res.scalar_one_or_none()
        tgt_res = await self.db.execute(select(Person).where(Person.id == target_person_id))
        target = tgt_res.scalar_one_or_none()

        if not source or not target:
            raise ValueError("Source or target person not found")

        # 2. Redirect Clients
        await self.db.execute(
            update(Client).where(Client.person_id == source_person_id).values(person_id=target_person_id)
        )

        # 3. Redirect Family Memberships
        await self.db.execute(
            update(FamilyMember).where(FamilyMember.person_id == source_person_id).values(person_id=target_person_id)
        )

        # 4. Redirect Family Relationships
        await self.db.execute(
            update(FamilyRelationship)
            .where(FamilyRelationship.person_a_id == source_person_id)
            .values(person_a_id=target_person_id)
        )
        await self.db.execute(
            update(FamilyRelationship)
            .where(FamilyRelationship.person_b_id == source_person_id)
            .values(person_b_id=target_person_id)
        )

        # 5. Redirect Household Memberships
        await self.db.execute(
            update(HouseholdMembership)
            .where(HouseholdMembership.person_id == source_person_id)
            .values(person_id=target_person_id)
        )

        # 6. Soft-delete source person (never destroy historical ID)
        source.deleted_at = target.updated_at

        # 7. Record Immutable Merge Log
        merge_record = PersonMerge(
            source_person_id=source_person_id,
            target_person_id=target_person_id,
            merged_by=merged_by,
            reason=reason,
            notes=notes,
        )
        self.db.add(merge_record)

        # 8. Record Compliance Audit Event
        audit = AuditService(self.db)
        await audit.log_event(
            event_type="PERSON_MERGED",
            user_id=merged_by,
            entity_type="person",
            entity_id=target_person_id,
            metadata={
                "source_person_id": str(source_person_id),
                "target_person_id": str(target_person_id),
                "reason": reason,
            },
        )

        await self.db.flush()
        return merge_record
