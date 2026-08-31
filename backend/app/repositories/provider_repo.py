"""Provider pool repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.provider import ClientProvider, Provider
from app.repositories.base import BaseRepository


class ProviderRepository(BaseRepository[Provider]):
    def __init__(self, db: AsyncSession):
        super().__init__(Provider, db)

    async def list_providers(
        self,
        query_text: str | None = None,
        provider_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Provider], int]:
        query = (
            select(Provider)
            .where(Provider.is_active == True)  # noqa: E712
            .options(
                selectinload(Provider.locations),
                selectinload(Provider.specialties),
            )
        )

        if provider_type:
            query = query.where(Provider.provider_type == provider_type)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(Provider.name.ilike(search_pattern) | Provider.organization_name.ilike(search_pattern))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(Provider.name.asc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def link_client_provider(
        self, client_id: uuid.UUID, provider_id: uuid.UUID, role: str = "Primary Care", notes: str = ""
    ) -> ClientProvider:
        link = ClientProvider(
            client_id=client_id,
            provider_id=provider_id,
            role=role,
            is_active=True,
            notes=notes,
        )
        self.db.add(link)
        await self.db.flush()
        return link

    async def list_client_providers(self, client_id: uuid.UUID) -> list[ClientProvider]:
        query = (
            select(ClientProvider)
            .where(ClientProvider.client_id == client_id)
            .options(selectinload(ClientProvider.provider))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
