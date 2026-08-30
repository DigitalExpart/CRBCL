"""Base repository class providing generic async CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: uuid.UUID) -> ModelType | None:
        """Fetch by primary key."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        include_deleted: bool = False,
    ) -> tuple[list[ModelType], int]:
        """Fetch paginated records with total count."""
        query = select(self.model)

        # Soft delete filtering
        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        # Simple field equality filters
        if filters:
            for k, v in filters.items():
                if hasattr(self.model, k) and v is not None:
                    query = query.where(getattr(self.model, k) == v)

        # Count total matching
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Sorting
        if sort_by:
            is_desc = sort_by.startswith("-")
            field = sort_by[1:] if is_desc else sort_by
            if hasattr(self.model, field):
                col = getattr(self.model, field)
                query = query.order_by(col.desc() if is_desc else col.asc())
        elif hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create(self, **data: Any) -> ModelType:
        """Instantiate and persist a new model."""
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def update(self, instance: ModelType, **data: Any) -> ModelType:
        """Update fields on an existing model."""
        for k, v in data.items():
            if hasattr(instance, k) and v is not None:
                setattr(instance, k, v)
        if hasattr(instance, "version") and instance.version is not None:
            instance.version += 1
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return instance

    async def soft_delete(self, instance: ModelType) -> ModelType:
        """Soft delete if model supports deleted_at, otherwise hard delete."""
        if hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.now(timezone.utc)
            await self.db.flush()
            return instance
        else:
            await self.db.delete(instance)
            await self.db.flush()
            return instance
