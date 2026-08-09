"""Integration tests — sync engine writes sync_runs / sync_jobs records.

Verifies T04 (partial-run durability):
- A RUNNING row is committed before any job executes (visible mid-run).
- Each completed job gets a committed sync_jobs row (per-job commit).
- The run row is finalized with status, rollup metrics, and error.
- Completed jobs survive a later mid-run failure (CANCELLED run keeps them).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.sync.job import SyncJob


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


class FakeProvider:
    """Minimal provider — the engine only needs provider_slug."""

    provider_slug = "fake"


class FakeSyncJob(SyncJob):
    """Fake job with injectable fetch failure and a DB probe in _upsert."""

    def __init__(self, entity_type, dtos=None, raise_on_fetch=False):
        super().__init__()
        self.entity_type = entity_type
        self.depends_on = []
        self.critical = True
        self.batch_size = 500
        self.supports_incremental = False
        self._dtos = dtos if dtos is not None else []
        self._raise_on_fetch = raise_on_fetch
        self.seen_run_status: list[str] = []

    async def _fetch(self, ctx, state):
        if self._raise_on_fetch:
            raise RuntimeError("simulated fetch failure")
        return self._dtos

    async def _upsert(self, ctx, batch):
        if ctx.db is not None:
            from sqlalchemy import select

            from src.db.models.support import SyncRun
            run = (await ctx.db.execute(select(SyncRun))).scalars().first()
            if run is not None:
                self.seen_run_status.append(run.status)
        return {"inserted": 10, "updated": 2, "skipped": 1, "errors": 0}


def _make_plan(order):
    from src.sync.plan import SyncPlan

    return SyncPlan(name="fake_plan", order=order)


async def _build_engine(jobs):
    from src.sync.engine import SyncEngine

    return SyncEngine(jobs=jobs)


@pytest.mark.asyncio
async def test_run_and_job_rows_recorded(db_session):
    """A completed run persists one sync_runs row + one sync_jobs row."""
    from sqlalchemy import select

    from src.db.models.support import SyncJob as SyncJobRecord
    from src.db.models.support import SyncRun
    from src.sync.types import EntityType, SyncMode

    job = FakeSyncJob(EntityType.FIGHTER, dtos=[{"id": 1}])
    engine = await _build_engine({EntityType.FIGHTER: job})
    plan = _make_plan([EntityType.FIGHTER])

    result = await engine.execute(
        plan=plan, provider=FakeProvider(), db_session=db_session, mode=SyncMode.FULL
    )

    assert result.overall_status.value == "COMPLETED"
    assert job.seen_run_status == ["RUNNING"]

    run = (await db_session.execute(select(SyncRun))).scalars().first()
    assert run is not None
    assert run.id == result.run_id
    assert run.status == "COMPLETED"
    assert run.mode == "full"
    assert run.provider == "fake"
    assert run.completed_at is not None
    assert run.error is None
    assert run.total_inserted == 10
    assert run.total_updated == 2
    assert run.total_skipped == 1
    assert run.total_errors == 0
    assert run.duration_ms >= 0

    job_row = (await db_session.execute(select(SyncJobRecord))).scalars().first()
    assert job_row is not None
    assert job_row.sync_run_id == result.run_id
    assert job_row.entity_type == "fighter"
    assert job_row.status == "COMPLETED"
    assert job_row.records_inserted == 10
    assert job_row.records_updated == 2
    assert job_row.records_skipped == 1
    assert job_row.records_errors == 0
    assert job_row.error is None


@pytest.mark.asyncio
async def test_completed_jobs_survive_mid_run_failure(db_session):
    """Job rows for finished jobs persist even when a later job fails."""
    from sqlalchemy import select

    from src.db.models.support import SyncJob as SyncJobRecord
    from src.db.models.support import SyncRun
    from src.sync.types import EntityType

    job1 = FakeSyncJob(EntityType.FIGHTER, dtos=[{"id": 1}])
    job2 = FakeSyncJob(EntityType.PROMOTION, raise_on_fetch=True)
    engine = await _build_engine({EntityType.FIGHTER: job1, EntityType.PROMOTION: job2})
    plan = _make_plan([EntityType.FIGHTER, EntityType.PROMOTION])

    result = await engine.execute(
        plan=plan, provider=FakeProvider(), db_session=db_session
    )

    assert result.overall_status.value == "FAILED"
    assert job1.seen_run_status == ["RUNNING"]

    run = (await db_session.execute(select(SyncRun))).scalars().first()
    assert run.status == "FAILED"
    assert run.completed_at is not None
    assert run.error is not None
    assert "simulated fetch failure" in run.error
    assert run.total_inserted == 10

    job_rows = (await db_session.execute(select(SyncJobRecord))).scalars().all()
    assert len(job_rows) == 2
    by_entity = {row.entity_type: row for row in job_rows}
    assert by_entity["fighter"].status == "COMPLETED"
    assert by_entity["promotion"].status == "FAILED"
    assert by_entity["promotion"].error is not None
    assert "simulated fetch failure" in by_entity["promotion"].error


@pytest.mark.asyncio
async def test_no_db_session_still_executes(db_session):
    """Engine still works when no DB session is provided (no records written)."""
    from src.sync.types import EntityType

    job = FakeSyncJob(EntityType.FIGHTER, dtos=[{"id": 1}])
    engine = await _build_engine({EntityType.FIGHTER: job})
    plan = _make_plan([EntityType.FIGHTER])

    result = await engine.execute(plan=plan, provider=FakeProvider())

    assert result.overall_status.value == "COMPLETED"
    assert result.total_inserted == 10
