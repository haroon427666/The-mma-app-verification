"""Unit of Work — transactional boundary for all repositories.

Usage:
    async with UnitOfWork() as uow:
        fighter = await uow.fighters.upsert(dto)
        await uow.fighters.upsert_record(fighter.id, record)
        await uow.commit()

    # rollback on exception — automatic
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session_factory
from src.db.repositories.fighter import FighterRepository
from src.db.repositories.events import (
    EventRepository, CompetitionRepository, PromotionRepository,
    VenueRepository, RankingRepository, WeightClassRepository, BroadcastRepository,
)


class UnitOfWork:
    """Manages a database transaction with all repositories."""

    def __init__(self, session: AsyncSession | None = None):
        self._external_session = session is not None
        self._session = session

    async def __aenter__(self) -> "UnitOfWork":
        if self._session is None:
            self._session = async_session_factory()
        self.fighters = FighterRepository(self._session)
        self.events = EventRepository(self._session)
        self.competitions = CompetitionRepository(self._session)
        self.promotions = PromotionRepository(self._session)
        self.venues = VenueRepository(self._session)
        self.rankings = RankingRepository(self._session)
        self.weight_classes = WeightClassRepository(self._session)
        self.broadcasts = BroadcastRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self._session.rollback()
            if not self._external_session:
                await self._session.close()
            return False  # Propagate exception

        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        finally:
            if not self._external_session:
                await self._session.close()

    async def commit(self):
        """Explicit commit mid-transaction."""
        await self._session.commit()

    async def rollback(self):
        """Explicit rollback."""
        await self._session.rollback()

    async def flush(self):
        """Flush pending changes to DB (for getting IDs)."""
        await self._session.flush()
