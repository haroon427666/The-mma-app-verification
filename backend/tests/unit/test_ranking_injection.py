"""Ranking → athlete injection tests.

Verifies the bounded, idempotent injection of unsynced ranked fighters into
the normal fighter pipeline (FighterUpsert + discovery registry consumed rows).
In-memory SQLite, no live DB.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.providers.dto import FighterDTO, RankingDTO


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models
        import src.db.models.support  # noqa: F401
        from src.db.base import Base
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


class FakeProvider:
    def __init__(self):
        self._config = SimpleNamespace(max_concurrency=4)
        self.fetched: list[list[str]] = []
        self.profiles: dict[str, FighterDTO] = {}

    def seed_profile(self, external_id: str) -> None:
        self.profiles[external_id] = FighterDTO(
            provider="espn",
            external_id=external_id,
            first_name="First",
            last_name=external_id,
        )

    async def fetch_fighters_by_ids(self, athlete_ids):
        self.fetched.append(list(athlete_ids))
        return [self.profiles[eid] for eid in athlete_ids if eid in self.profiles]

    async def fetch_fighter_record(self, external_id):
        return None  # content-dependent empty → attach_records skips


def make_rankings(*external_ids: str) -> list[RankingDTO]:
    return [
        RankingDTO(
            provider="espn",
            fighter_external_id=eid,
            promotion_external_id="ufc",
            category="heavyweight",
            rank=i,
        )
        for i, eid in enumerate(external_ids, start=1)
    ]


def make_ctx(session, provider, run_id="run-1"):
    return SimpleNamespace(
        db=session,
        provider=provider,
        run_id=run_id,
    )


async def known_fighter_ids(session) -> set[str]:
    from sqlalchemy import select

    from src.db.models.support import ExternalId

    result = await session.execute(
        select(ExternalId.external_id).where(
            ExternalId.provider == "espn", ExternalId.entity_type == "fighter"
        )
    )
    return {str(r) for r in result.scalars().all()}


class TestRankingInjection:
    @pytest.mark.asyncio
    async def test_injects_missing_and_registers_consumed(self, db_session):
        from src.sync.upserts.id_resolver import IdResolver

        provider = FakeProvider()
        provider.seed_profile("3000001")
        provider.seed_profile("3000002")

        # 3000001 already synced (external_id mapping exists)
        resolver = IdResolver(db_session)
        await resolver.register("espn", "3000001", "fighter", "11111111-1111-1111-1111-111111111111")
        await db_session.flush()

        from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob

        job = ESPN_RankingSyncJob()
        await job._inject_missing_fighters(
            make_ctx(db_session, provider), make_rankings("3000001", "3000002")
        )
        await db_session.commit()

        # Only the missing fighter was fetched + created
        assert provider.fetched == [["3000002"]]
        assert "3000002" in await known_fighter_ids(db_session)

        # Registry: consumed row with source='rankings' (no pending ids)
        from sqlalchemy import select

        from src.db.models.support import SyncDiscoveredAthlete

        result = await db_session.execute(
            select(SyncDiscoveredAthlete).where(
                SyncDiscoveredAthlete.external_id == "3000002"
            )
        )
        row = result.scalar_one()
        assert row.source == "rankings"
        assert row.consumed is True
        assert row.run_id == "run-1"

        from src.providers.espn.discovery import DiscoveryService

        assert await DiscoveryService(session=db_session).pending_count() == 0

    @pytest.mark.asyncio
    async def test_all_synced_skips_fetch(self, db_session):
        from src.sync.upserts.id_resolver import IdResolver

        provider = FakeProvider()
        resolver = IdResolver(db_session)
        await resolver.register("espn", "3000001", "fighter", "11111111-1111-1111-1111-111111111111")
        await db_session.flush()

        from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob

        job = ESPN_RankingSyncJob()
        await job._inject_missing_fighters(
            make_ctx(db_session, provider), make_rankings("3000001")
        )
        assert provider.fetched == []  # no work

    @pytest.mark.asyncio
    async def test_limit_bounds_injection(self, db_session, monkeypatch):
        provider = FakeProvider()
        for eid in ("3000001", "3000002", "3000003"):
            provider.seed_profile(eid)
        monkeypatch.setenv("ESPN_RANKING_INJECTION_LIMIT", "2")

        from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob

        job = ESPN_RankingSyncJob()
        await job._inject_missing_fighters(
            make_ctx(db_session, provider), make_rankings("3000001", "3000002", "3000003")
        )
        assert provider.fetched == [["3000001", "3000002"]]  # capped at 2

    @pytest.mark.asyncio
    async def test_disabled_when_zero(self, db_session, monkeypatch):
        provider = FakeProvider()
        provider.seed_profile("3000001")
        monkeypatch.setenv("ESPN_RANKING_INJECTION_LIMIT", "0")

        from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob

        job = ESPN_RankingSyncJob()
        await job._inject_missing_fighters(
            make_ctx(db_session, provider), make_rankings("3000001")
        )
        assert provider.fetched == []  # disabled

    @pytest.mark.asyncio
    async def test_rejects_fake_ids(self, db_session):
        """Only real refs (ids present in the ranking DTOs) are injected."""
        provider = FakeProvider()  # NO profiles seeded → fetch resolves nothing
        from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob

        job = ESPN_RankingSyncJob()
        await job._inject_missing_fighters(
            make_ctx(db_session, provider), make_rankings("3000001")
        )
        await db_session.commit()

        assert await known_fighter_ids(db_session) == set()  # nothing fabricated
        from sqlalchemy import func, select

        from src.db.models.support import SyncDiscoveredAthlete

        result = await db_session.execute(
            select(func.count()).select_from(SyncDiscoveredAthlete)
        )
        assert int(result.scalar_one()) == 0

    @pytest.mark.asyncio
    async def test_job_fetch_injects_then_returns_rankings(self, db_session, monkeypatch):
        """End-to-end: job._fetch injects missing fighters BEFORE returning
        dtos, so the same run's RankingUpsert can resolve them."""
        provider = FakeProvider()
        provider.seed_profile("3000001")

        from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob

        async def fake_promotions():
            return [SimpleNamespace(external_id="ufc")]

        async def fake_rankings(slug):
            return make_rankings("3000001")

        provider.fetch_promotions = fake_promotions
        provider.fetch_rankings = fake_rankings

        job = ESPN_RankingSyncJob()
        dtos = await job._fetch(make_ctx(db_session, provider), state=None)
        await db_session.commit()

        assert len(dtos) == 1
        assert "3000001" in await known_fighter_ids(db_session)
