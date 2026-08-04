"""FastAPI dependencies — DB session, pagination, cache."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Query

from src.db.session import get_session
from src.middleware.cache import CacheManager, default_cache
from src.schemas.common import PaginationParams, SortParams

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.db.unit_of_work import UnitOfWork

# Re-export
DatabaseSession = Annotated[object, Depends(get_session)]


def pagination(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


def sorting(
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
) -> SortParams:
    return SortParams(sort_by=sort_by, sort_dir=sort_dir)


# Composite dependency
Pagination = Annotated[PaginationParams, Depends(pagination)]
Sorting = Annotated[SortParams, Depends(sorting)]


# ── Database session dependency ───────────────────────────────────

async def get_uow() -> AsyncIterator[UnitOfWork]:
    """Yields a UnitOfWork wrapping a database transaction."""
    from src.db.unit_of_work import UnitOfWork
    async with UnitOfWork() as uow:
        yield uow


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yields a raw async database session (for read-only queries)."""
    from src.db.session import async_session_factory
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


UnitOfWorkDep = Annotated["UnitOfWork", Depends(get_uow)]
DbSessionDep = Annotated["AsyncSession", Depends(get_db_session)]


# ── Cache dependency ───────────────────────────────────────────────────

async def get_cache_manager() -> CacheManager:
    """Return the process-wide cache backend (memory or Redis)."""
    return default_cache()


CacheDep = Annotated[CacheManager, Depends(get_cache_manager)]
