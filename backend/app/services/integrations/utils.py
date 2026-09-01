"""Database Async / Sync Session Compatibility Utilities for Integration Services."""

from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def db_query_first(db: Any, model: type[T], *criterion: Any) -> T | None:
    """Query single record compatible with both AsyncSession and sync Session."""
    stmt = select(model).where(*criterion)
    if isinstance(db, AsyncSession):
        res = await db.execute(stmt)
        return res.scalars().first()
    return db.query(model).filter(*criterion).first()


async def db_query_all(db: Any, model: type[T], *criterion: Any) -> list[T]:
    """Query multiple records compatible with both AsyncSession and sync Session."""
    stmt = select(model).where(*criterion)
    if isinstance(db, AsyncSession):
        res = await db.execute(stmt)
        return list(res.scalars().all())
    return db.query(model).filter(*criterion).all()


async def db_commit(db: Any) -> None:
    """Commit transaction compatible with both AsyncSession and sync Session."""
    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()


async def db_refresh(db: Any, obj: Any) -> None:
    """Refresh instance compatible with both AsyncSession and sync Session."""
    if isinstance(db, AsyncSession):
        await db.refresh(obj)
    else:
        db.refresh(obj)
