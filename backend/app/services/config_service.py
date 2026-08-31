"""Configuration and Lookup service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.config import LookupList, LookupValue, SystemConfig


class ConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lookup_values(self, list_key: str, active_only: bool = True) -> list[LookupValue]:
        """Fetch all lookup values for a given list key, ordered by sort_order."""
        query = select(LookupList).where(LookupList.key == list_key).options(selectinload(LookupList.values))
        result = await self.db.execute(query)
        lookup_list = result.scalar_one_or_none()
        if not lookup_list or not lookup_list.is_active:
            return []

        values = lookup_list.values
        if active_only:
            values = [v for v in values if v.is_active]
        return sorted(values, key=lambda v: v.sort_order)

    async def get_config_value(self, key: str, default: str = "") -> str:
        """Fetch system configuration value by key."""
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        cfg = result.scalar_one_or_none()
        if cfg:
            return cfg.value
        return default

    async def set_config_value(
        self,
        key: str,
        value: str,
        description: str = "",
        value_type: str = "string",
        is_sensitive: bool = False,
        updated_by: uuid.UUID | None = None,
    ) -> SystemConfig:
        """Create or update system configuration."""
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        cfg = result.scalar_one_or_none()
        if cfg:
            cfg.value = value
            cfg.updated_by = updated_by
        else:
            cfg = SystemConfig(
                key=key,
                value=value,
                description=description,
                value_type=value_type,
                is_sensitive=is_sensitive,
                updated_by=updated_by,
            )
            self.db.add(cfg)
        await self.db.flush()
        return cfg
