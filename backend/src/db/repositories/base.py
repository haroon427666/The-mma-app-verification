"""Base repository — shared CRUD for all entities.

Hides SQLAlchemy completely from business logic.
All methods accept DTOs and return domain models or counts.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic async repository with idempotent upsert support."""

    model: type[T]

    def __init__(self, session: AsyncSession):
        self._session = session

    # ── Read ────────────────────────────────────────────────────────────

    async def get_by_id(self, entity_id: str) -> T | None:
        result = await self._session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, provider: str, external_id: str) -> T | None:
        result = await self._session.execute(
            select(self.model).where(
                self.model.provider == provider,
                self.model.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 1000, offset: int = 0) -> list[T]:
        result = await self._session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    # ── Write — idempotent upsert ───────────────────────────────────────

    async def upsert(self, dto: Any) -> T:
        """Idempotent insert or update. Returns the entity."""
        # Build insert values from DTO
        values = self._dto_to_values(dto)

        stmt = insert(self.model).values(**values).on_conflict_do_update(
            constraint=f"uq_{self.model.__tablename__}_provider_external",
            set_=self._upsert_update_values(values),
        ).returning(self.model)

        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()

    async def upsert_batch(self, dtos: list[Any], batch_size: int = 500) -> int:
        """Batch upsert — returns count of rows affected."""
        affected = 0
        for i in range(0, len(dtos), batch_size):
            batch = dtos[i:i + batch_size]
            values_list = [self._dto_to_values(d) for d in batch]

            stmt = insert(self.model).values(values_list).on_conflict_do_update(
                constraint=f"uq_{self.model.__tablename__}_provider_external",
                set_=self._upsert_update_values(values_list[0]),
            )

            result = await self._session.execute(stmt)
            affected += result.rowcount
            await self._session.flush()

        return affected

    async def update_fields(self, entity_id: str, **fields) -> None:
        """Update specific fields on an entity."""
        stmt = (
            update(self.model)
            .where(self.model.id == entity_id)
            .values(**fields)
        )
        await self._session.execute(stmt)

    # ── Subclass hooks ──────────────────────────────────────────────────

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        """Convert a DTO to a dict of column values. Override per entity."""
        raise NotImplementedError

    def _upsert_update_values(self, values: dict) -> dict:
        """Fields to update on conflict. Excludes PK and identity columns.
        By default, updates everything except provider and external_id.
        """
        skip = {"id", "provider", "external_id", "created_at"}
        return {k: v for k, v in values.items() if k not in skip}


class NoResultFound(Exception):
    pass
