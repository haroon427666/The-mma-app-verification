"""Unit of Work — transactional boundary for all repositories.

Usage:
    async with UnitOfWork() as uow:
        fighter = await uow.fighters.upsert(dto)
        await uow.fighters.upsert_record(fighter.id, record)
        await uow.commit()

    # rollback on exception — automatic
"""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.events import (
    BroadcastRepository,
    CompetitionRepository,
    EventRepository,
    PromotionRepository,
    RankingRepository,
    VenueRepository,
    WeightClassRepository,
)
from src.db.repositories.fighter import FighterRepository
from src.db.session import async_session_factory


class UnitOfWork:
    """Manages a database transaction with all repositories."""

    def __init__(self, session: AsyncSession | None = None):
        self._external_session = session is not None
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """The active session. Raises if the unit of work is not entered."""
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered — call 'async with UnitOfWork()' first")
        return self._session

    async def __aenter__(self) -> Self:
        if self._session is None:
            self._session = async_session_factory()
        session = self.session
        self.fighters = FighterRepository(session)
        self.events = EventRepository(session)
        self.competitions = CompetitionRepository(session)
        self.promotions = PromotionRepository(session)
        self.venues = VenueRepository(session)
        self.rankings = RankingRepository(session)
        self.weight_classes = WeightClassRepository(session)
        self.broadcasts = BroadcastRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        session = self.session
        if exc_type is not None:
            await session.rollback()
            if not self._external_session:
                await session.close()
            return False  # Propagate exception

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if not self._external_session:
                await session.close()
        return False

    async def commit(self) -> None:
        """Explicit commit mid-transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Explicit rollback."""
        await self.session.rollback()

    async def flush(self) -> None:
        """Flush pending changes to DB (for getting IDs)."""
        await self.session.flush()
