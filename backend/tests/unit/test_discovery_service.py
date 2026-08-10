"""DiscoveryService tests — resumable census, registry, window, consumption.

Runs on in-memory SQLite (no live DB, no network). The discovery service's
ON CONFLICT inserts are dialect-portable (Postgres prod / SQLite tests).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.providers.espn.config import ENDPOINTS


@pytest.fixture
async def db_session():
    """In-memory SQLite session for test isolation."""
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


@pytest.fixture
def league_env(monkeypatch):
    monkeypatch.setenv("ESPN_SYNC_LEAGUES", "ufc")


GLOBAL_PATH = ENDPOINTS["global_athletes"]
ROSTER_UFC_PATH = ENDPOINTS["athletes"].format(league_slug="ufc")


def ref(eid: str) -> dict:
    return {"$ref": f"https://sports.core.api.espn.com/v2/sports/mma/athletes/{eid}"}


def page(*eids: str) -> dict:
    return {"items": [ref(e) for e in eids]}


class FakePaginator:
    """Client stand-in: pages per path, optional failure, records calls."""

    def __init__(self, pages_by_path: dict, fail_at=None):
        self.pages_by_path = pages_by_path
        self.fail_at = fail_at  # (path, page_number) → raise
        self.calls: list[tuple[str, int]] = []

    async def paginate(self, path, params=None, limit=None, start_page=1):
        self.calls.append((path, start_page))
        pages = self.pages_by_path.get(path, [])
        for idx in range(start_page - 1, len(pages)):
            if self.fail_at and self.fail_at[0] == path and (idx + 1) == self.fail_at[1]:
                raise RuntimeError(f"boom {path} page {idx + 1}")
            yield pages[idx]


class FakeProvider:
    def __init__(self, client):
        self._client = client


def make_service(session, paginator):
    from src.providers.espn.discovery import DiscoveryService

    return DiscoveryService(session=session, provider=FakeProvider(paginator))


async def registry_ids(session) -> list[str]:
    from sqlalchemy import select

    from src.db.models.support import SyncDiscoveredAthlete

    result = await session.execute(
        select(SyncDiscoveredAthlete.external_id).order_by(SyncDiscoveredAthlete.id)
    )
    return [str(r) for r in result.scalars().all()]


async def checkpoint_pages(session) -> dict:
    from sqlalchemy import select

    from src.db.models.support import SyncDiscoveryCheckpoint

    result = await session.execute(select(SyncDiscoveryCheckpoint))
    return {
        (row.source, row.league_slug): (row.page, row.completed, row.status)
        for row in result.scalars().all()
    }


class TestWalkCompletes:
    @pytest.mark.asyncio
    async def test_walk_populates_registry_and_completes_sources(self, db_session, league_env):
        paginator = FakePaginator({
            GLOBAL_PATH: [page("2000001", "2000002"), page("2000003")],
            ROSTER_UFC_PATH: [page("2000002", "2000004")],  # shares one id
        })
        service = make_service(db_session, paginator)

        summaries = await service.ensure_enumerated(run_id="run-1")

        assert len(summaries) == 2
        assert all(s.completed for s in summaries)
        assert all(s.skipped is False for s in summaries)
        # Dedup across sources: 2000002 appears twice → 4 unique ids
        assert sorted(await registry_ids(db_session)) == [
            "2000001", "2000002", "2000003", "2000004",
        ]
        assert await service.pending_count() == 4
        assert await service.registry_count() == 4
        pages = await checkpoint_pages(db_session)
        assert pages[("global_listing", "")] == (2, True, "COMPLETED")
        assert pages[("roster", "ufc")] == (1, True, "COMPLETED")

    @pytest.mark.asyncio
    async def test_completed_sources_are_skipped(self, db_session, league_env):
        paginator = FakePaginator({
            GLOBAL_PATH: [page("2000001"), page("2000002")],
            ROSTER_UFC_PATH: [page("2000003")],
        })
        service = make_service(db_session, paginator)

        await service.ensure_enumerated(run_id="run-1")
        paginator.calls.clear()
        summaries = await service.ensure_enumerated(run_id="run-2")

        assert paginator.calls == []  # no walk requests at all
        assert all(s.skipped for s in summaries)

    @pytest.mark.asyncio
    async def test_force_rewalks_completed_sources(self, db_session, league_env):
        paginator = FakePaginator({
            GLOBAL_PATH: [page("2000001")],
            ROSTER_UFC_PATH: [page("2000002")],
        })
        service = make_service(db_session, paginator)

        await service.ensure_enumerated(run_id="run-1")
        paginator.calls.clear()
        summaries = await service.ensure_enumerated(run_id="run-2", force=True)

        assert len(paginator.calls) == 2  # re-walked
        assert not any(s.skipped for s in summaries)
        assert sorted(await registry_ids(db_session)) == ["2000001", "2000002"]


class TestWalkResume:
    @pytest.mark.asyncio
    async def test_interrupted_walk_resumes_from_next_page(self, db_session, league_env):
        paginator = FakePaginator(
            {GLOBAL_PATH: [page("2000001"), page("2000002"), page("2000003")],
             ROSTER_UFC_PATH: [page("2000004")]},
            fail_at=(GLOBAL_PATH, 2),
        )
        service = make_service(db_session, paginator)

        # Run 1: global listing dies on page 2 → source FAILED, roster NOT walked
        summaries = await service.ensure_enumerated(run_id="run-1")
        failed = next(s for s in summaries if s.source == "global_listing")
        assert failed.completed is False
        pages = await checkpoint_pages(db_session)
        assert pages[("global_listing", "")][0] == 1  # last processed page
        assert pages[("global_listing", "")][1] is False

        # Run 2: resumes global at page 2 (NO page-1 restart), roster walked fresh
        paginator.fail_at = None
        paginator.calls.clear()
        summaries = await service.ensure_enumerated(run_id="run-2")

        global_calls = [c for c in paginator.calls if c[0] == GLOBAL_PATH]
        assert global_calls == [(GLOBAL_PATH, 2)]
        assert all(s.completed for s in summaries)
        assert sorted(await registry_ids(db_session)) == [
            "2000001", "2000002", "2000003", "2000004",
        ]

    @pytest.mark.asyncio
    async def test_partial_page_inserts_are_not_duplicated(self, db_session, league_env):
        """A page whose ids were committed but whose checkpoint was not saved
        re-inserts them idempotently (ON CONFLICT DO NOTHING)."""
        from sqlalchemy import func, select

        from src.db.models.support import SyncDiscoveredAthlete

        paginator = FakePaginator(
            {GLOBAL_PATH: [page("2000001", "2000002")], ROSTER_UFC_PATH: []},
        )
        service = make_service(db_session, paginator)
        await service.register_ids(["2000001"], source="global_listing")  # pre-seeded
        await db_session.commit()

        await service.ensure_enumerated(run_id="run-1")

        result = await db_session.execute(
            select(func.count()).select_from(SyncDiscoveredAthlete)
        )
        assert int(result.scalar_one()) == 2


class TestWindow:
    @pytest.mark.asyncio
    async def test_window_is_unconsumed_ascending_and_bounded(self, db_session, league_env):
        paginator = FakePaginator({
            GLOBAL_PATH: [page("2000003", "2000001", "2000002")],  # insertion order ≠ sorted
            ROSTER_UFC_PATH: [],
        })
        service = make_service(db_session, paginator)
        await service.ensure_enumerated()

        window = await service.next_window(limit=2)
        assert window == ["2000001", "2000002"]  # ascending, bounded
        assert await service.next_window(limit=None) == [
            "2000001", "2000002", "2000003",
        ]

    @pytest.mark.asyncio
    async def test_late_arrival_is_always_selected(self, db_session, league_env):
        """An id registered AFTER consumption of higher ids is still picked up
        (the window is a filter on unconsumed ids, not an offset cursor)."""
        paginator = FakePaginator({
            GLOBAL_PATH: [page("2000001", "2000002")], ROSTER_UFC_PATH: [],
        })
        service = make_service(db_session, paginator)
        await service.ensure_enumerated()
        await service.mark_consumed(["2000001", "2000002"])

        # Relationship surface adds a low id late
        await service.register_ids(["2000000"], source="competition")
        await db_session.commit()

        assert await service.next_window(limit=None) == ["2000000"]

    @pytest.mark.asyncio
    async def test_mark_consumed_empties_window(self, db_session, league_env):
        paginator = FakePaginator({
            GLOBAL_PATH: [page("2000001")], ROSTER_UFC_PATH: [],
        })
        service = make_service(db_session, paginator)
        await service.ensure_enumerated()

        assert await service.next_window(limit=None) == ["2000001"]
        await service.mark_consumed(["2000001"])
        assert await service.next_window(limit=None) == []


class TestRegister:
    @pytest.mark.asyncio
    async def test_first_source_wins(self, db_session):
        from sqlalchemy import select

        from src.db.models.support import SyncDiscoveredAthlete

        service = make_service(db_session, FakePaginator({}))
        inserted = await service.register_ids(["2000001"], source="listing")
        assert inserted == 1
        second = await service.register_ids(["2000001"], source="competition")
        assert second == 0  # conflict ignored

        result = await db_session.execute(
            select(SyncDiscoveredAthlete).where(
                SyncDiscoveredAthlete.external_id == "2000001"
            )
        )
        row = result.scalar_one()
        assert row.source == "listing"

    @pytest.mark.asyncio
    async def test_consumed_flag_on_register(self, db_session):
        service = make_service(db_session, FakePaginator({}))
        await service.register_ids(["2000001"], source="rankings", consumed=True)
        await db_session.commit()
        assert await service.pending_count() == 0
        assert await service.registry_count() == 1
