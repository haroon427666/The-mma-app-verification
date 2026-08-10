"""DatabaseSyncStateStore + CheckpointManager data-payload tests.

In-memory SQLite, no live DB. Verifies the SyncState roundtrip through the
existing sync_checkpoints table (scalar columns + data JSON payload).
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.sync.types import EntityType


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


class TestCheckpointManagerData:
    @pytest.mark.asyncio
    async def test_save_load_roundtrip_with_data(self, db_session):
        from src.sync.checkpoints import Checkpoint, CheckpointManager

        manager = CheckpointManager(db_session)
        await manager.save(
            Checkpoint(
                entity_type="fighter", provider="espn",
                last_offset=2000, last_page=2, status="IN_PROGRESS",
            ),
            data={"checkpoint": {"nested": [1, 2]}, "flag": True},
        )
        await db_session.commit()

        loaded = await manager.load("fighter", "espn")
        assert loaded is not None
        assert loaded.last_offset == 2000
        assert loaded.data == {"checkpoint": {"nested": [1, 2]}, "flag": True}

    @pytest.mark.asyncio
    async def test_save_without_data_keeps_existing_payload(self, db_session):
        """Backward compatible: a save without data must not NULL the column."""
        from src.sync.checkpoints import Checkpoint, CheckpointManager

        manager = CheckpointManager(db_session)
        await manager.save(
            Checkpoint(entity_type="fighter", provider="espn"),
            data={"keep": "me"},
        )
        await manager.save(Checkpoint(entity_type="fighter", provider="espn", last_offset=5))
        await db_session.commit()

        loaded = await manager.load("fighter", "espn")
        assert loaded.data == {"keep": "me"}


class TestDatabaseSyncStateStore:
    @pytest.mark.asyncio
    async def test_load_returns_none_when_missing(self, db_session):
        from src.sync.state_store import DatabaseSyncStateStore

        store = DatabaseSyncStateStore(db_session)
        assert await store.load(EntityType.FIGHTER, "espn") is None

    @pytest.mark.asyncio
    async def test_roundtrip_preserves_state(self, db_session):
        from src.sync.state import SyncState
        from src.sync.state_store import DatabaseSyncStateStore

        store = DatabaseSyncStateStore(db_session)
        now = datetime.now(UTC)
        state = SyncState(
            entity_type=EntityType.FIGHTER,
            provider_slug="espn",
            last_successful_sync=now,
            last_attempt=now - timedelta(minutes=5),
            last_offset=2500,
            last_page=3,
            last_cursor="cursor-abc",
            checkpoint={"athlete_ids": ["1", "2"], "window": 10},
            status="COMPLETED",
            total_synced=2500,
            consecutive_failures=2,
        )
        await store.save(state)

        loaded = await store.load(EntityType.FIGHTER, "espn")
        assert loaded is not None
        assert loaded.entity_type == EntityType.FIGHTER
        assert loaded.provider_slug == "espn"
        assert loaded.last_successful_sync == now
        assert loaded.last_attempt == now - timedelta(minutes=5)
        assert loaded.last_offset == 2500
        assert loaded.last_page == 3
        assert loaded.last_cursor == "cursor-abc"
        assert loaded.checkpoint == {"athlete_ids": ["1", "2"], "window": 10}
        assert loaded.status == "COMPLETED"
        assert loaded.total_synced == 2500
        assert loaded.consecutive_failures == 2

        # Scalar columns are kept in sync for humans/tooling
        from src.sync.checkpoints import CheckpointManager

        raw = await CheckpointManager(db_session).load("fighter", "espn")
        assert raw.status == "COMPLETED"
        assert raw.completed is True

    @pytest.mark.asyncio
    async def test_overwrite_updates_same_row(self, db_session):
        from src.sync.state import SyncState
        from src.sync.state_store import DatabaseSyncStateStore

        store = DatabaseSyncStateStore(db_session)
        state = SyncState(entity_type=EntityType.FIGHTER, provider_slug="espn")
        state.mark_started(datetime.now(UTC))
        state.checkpoint = {"athlete_ids": ["a"]}
        await store.save(state)

        state.checkpoint = {"athlete_ids": ["a", "b"]}
        state.last_offset = 100
        await store.save(state)

        loaded = await store.load(EntityType.FIGHTER, "espn")
        assert loaded.checkpoint == {"athlete_ids": ["a", "b"]}
        assert loaded.last_offset == 100

    @pytest.mark.asyncio
    async def test_normalize_data_handles_json_strings(self):
        from src.sync.checkpoints import _normalize_data

        assert _normalize_data('{"a": 1}') == {"a": 1}
        assert _normalize_data({"a": 1}) == {"a": 1}
        assert _normalize_data(None) is None
        assert _normalize_data("not json") is None

    @pytest.mark.asyncio
    async def test_failed_state_survives_roundtrip(self, db_session):
        from src.sync.state import SyncState
        from src.sync.state_store import DatabaseSyncStateStore

        store = DatabaseSyncStateStore(db_session)
        state = SyncState(entity_type=EntityType.FIGHTER, provider_slug="espn")
        state.mark_failed(datetime.now(UTC), "boom")

        await store.save(state)
        loaded = await store.load(EntityType.FIGHTER, "espn")
        assert loaded.status == "FAILED"
        assert loaded.error_msg == "boom"
