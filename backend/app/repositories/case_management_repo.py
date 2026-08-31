"""Repositories for Case Management sub-entities: People, Assignments, External Workers, Sources, Links, Restrictions, Transfers, and Status History."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case_management import (
    CaseAssignment,
    CaseExternalWorker,
    CaseLink,
    CasePerson,
    CaseRestriction,
    CaseSource,
    CaseStatusHistory,
    CaseTransfer,
)
from app.repositories.base import BaseRepository


class CasePersonRepository(BaseRepository[CasePerson]):
    def __init__(self, db: AsyncSession):
        super().__init__(CasePerson, db)

    async def get_by_id_with_person(self, person_link_id: uuid.UUID) -> CasePerson | None:
        stmt = select(CasePerson).where(CasePerson.id == person_link_id).options(selectinload(CasePerson.person))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_case(self, case_id: uuid.UUID) -> list[CasePerson]:
        stmt = (
            select(CasePerson)
            .where(CasePerson.case_id == case_id, CasePerson.deleted_at.is_(None))
            .options(selectinload(CasePerson.person))
            .order_by(CasePerson.is_primary.desc(), CasePerson.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CaseAssignmentRepository(BaseRepository[CaseAssignment]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseAssignment, db)

    async def get_by_id_with_user(self, assignment_id: uuid.UUID) -> CaseAssignment | None:
        stmt = select(CaseAssignment).where(CaseAssignment.id == assignment_id).options(selectinload(CaseAssignment.user))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_case(self, case_id: uuid.UUID) -> list[CaseAssignment]:
        stmt = (
            select(CaseAssignment)
            .where(CaseAssignment.case_id == case_id)
            .options(selectinload(CaseAssignment.user))
            .order_by(CaseAssignment.is_active.desc(), CaseAssignment.assigned_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def deactivate_previous_role_assignment(self, case_id: uuid.UUID, role: str) -> None:
        """Deactivate existing active worker with same role (e.g. primary investigator)."""
        stmt = select(CaseAssignment).where(
            CaseAssignment.case_id == case_id,
            CaseAssignment.role == role,
            CaseAssignment.is_active == True,  # noqa: E712
        )
        res = await self.db.execute(stmt)
        for assignment in res.scalars().all():
            assignment.is_active = False
            assignment.unassigned_at = datetime.now(timezone.utc)
        await self.db.flush()


class CaseExternalWorkerRepository(BaseRepository[CaseExternalWorker]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseExternalWorker, db)

    async def get_by_case(self, case_id: uuid.UUID) -> list[CaseExternalWorker]:
        stmt = (
            select(CaseExternalWorker)
            .where(CaseExternalWorker.case_id == case_id, CaseExternalWorker.deleted_at.is_(None))
            .order_by(CaseExternalWorker.is_active.desc(), CaseExternalWorker.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CaseSourceRepository(BaseRepository[CaseSource]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseSource, db)

    async def get_by_case(self, case_id: uuid.UUID, category: str | None = None) -> list[CaseSource]:
        stmt = select(CaseSource).where(CaseSource.case_id == case_id, CaseSource.deleted_at.is_(None))
        if category:
            stmt = stmt.where(CaseSource.category == category)
        stmt = stmt.options(selectinload(CaseSource.person), selectinload(CaseSource.provider)).order_by(
            CaseSource.created_at.desc()
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CaseLinkRepository(BaseRepository[CaseLink]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseLink, db)

    async def get_by_id_with_cases(self, link_id: uuid.UUID) -> CaseLink | None:
        stmt = (
            select(CaseLink)
            .where(CaseLink.id == link_id)
            .options(selectinload(CaseLink.source_case), selectinload(CaseLink.target_case))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_case(self, case_id: uuid.UUID) -> list[CaseLink]:
        stmt = (
            select(CaseLink)
            .where(or_(CaseLink.source_case_id == case_id, CaseLink.target_case_id == case_id))
            .options(selectinload(CaseLink.source_case), selectinload(CaseLink.target_case))
            .order_by(CaseLink.linked_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def link_exists(self, case_a: uuid.UUID, case_b: uuid.UUID) -> bool:
        stmt = select(CaseLink).where(
            or_(
                (CaseLink.source_case_id == case_a) & (CaseLink.target_case_id == case_b),
                (CaseLink.source_case_id == case_b) & (CaseLink.target_case_id == case_a),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None


class CaseRestrictionRepository(BaseRepository[CaseRestriction]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseRestriction, db)

    async def get_by_id_with_user(self, restriction_id: uuid.UUID) -> CaseRestriction | None:
        stmt = select(CaseRestriction).where(CaseRestriction.id == restriction_id).options(selectinload(CaseRestriction.user))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_case(self, case_id: uuid.UUID, active_only: bool = False) -> list[CaseRestriction]:
        stmt = select(CaseRestriction).where(CaseRestriction.case_id == case_id)
        if active_only:
            stmt = stmt.where(CaseRestriction.is_active == True)  # noqa: E712
        stmt = stmt.options(selectinload(CaseRestriction.user)).order_by(CaseRestriction.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def is_user_restricted(self, case_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(CaseRestriction).where(
            CaseRestriction.case_id == case_id,
            CaseRestriction.user_id == user_id,
            CaseRestriction.is_active == True,  # noqa: E712
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None


class CaseTransferRepository(BaseRepository[CaseTransfer]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseTransfer, db)

    async def get_by_id_with_details(self, transfer_id: uuid.UUID) -> CaseTransfer | None:
        stmt = (
            select(CaseTransfer)
            .where(CaseTransfer.id == transfer_id)
            .options(
                selectinload(CaseTransfer.case),
                selectinload(CaseTransfer.child),
                selectinload(CaseTransfer.source_team),
                selectinload(CaseTransfer.destination_team),
                selectinload(CaseTransfer.requester),
                selectinload(CaseTransfer.reviewer),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_case(self, case_id: uuid.UUID) -> list[CaseTransfer]:
        stmt = (
            select(CaseTransfer)
            .where(CaseTransfer.case_id == case_id)
            .options(
                selectinload(CaseTransfer.child),
                selectinload(CaseTransfer.source_team),
                selectinload(CaseTransfer.destination_team),
                selectinload(CaseTransfer.requester),
                selectinload(CaseTransfer.reviewer),
            )
            .order_by(CaseTransfer.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_pending_transfers(self, team_ids: set[uuid.UUID] | None = None) -> list[CaseTransfer]:
        stmt = select(CaseTransfer).where(CaseTransfer.status == "PENDING_APPROVAL")
        if team_ids is not None:
            stmt = stmt.where(
                or_(
                    CaseTransfer.destination_team_id.in_(team_ids),
                    CaseTransfer.source_team_id.in_(team_ids),
                )
            )
        stmt = stmt.options(
            selectinload(CaseTransfer.case),
            selectinload(CaseTransfer.child),
            selectinload(CaseTransfer.source_team),
            selectinload(CaseTransfer.destination_team),
            selectinload(CaseTransfer.requester),
        ).order_by(CaseTransfer.requested_at.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


class CaseStatusHistoryRepository(BaseRepository[CaseStatusHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseStatusHistory, db)

    async def get_by_case(self, case_id: uuid.UUID) -> list[CaseStatusHistory]:
        stmt = (
            select(CaseStatusHistory)
            .where(CaseStatusHistory.case_id == case_id)
            .options(selectinload(CaseStatusHistory.changer))
            .order_by(CaseStatusHistory.changed_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
