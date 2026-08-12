"""Tests for sync → cache invalidation (src/sync/cache_invalidation.py)."""

import pytest

from src.middleware.cache import MemoryCacheManager
from src.sync import cache_invalidation
from src.sync.cache_invalidation import _prefixes_for, invalidate_after_sync
from src.sync.events import SyncEventCtx
from src.sync.job import JobResult
from src.sync.result import SyncResult
from src.sync.types import JobStatus, SyncStatus


@pytest.fixture(autouse=True)
def _memory_cache(monkeypatch: pytest.MonkeyPatch) -> MemoryCacheManager:
    mem = MemoryCacheManager()
    monkeypatch.setattr(cache_invalidation, "default_cache", lambda: mem)
    return mem


def _result(
    *,
    status: SyncStatus = SyncStatus.COMPLETED,
    jobs: list[JobResult] | None = None,
) -> SyncResult:
    return SyncResult(
        run_id="run-1",
        overall_status=status,
        job_results=jobs or [],
        started_at=None,
        completed_at=None,
        duration_ms=0.0,
    )


def _job(entity: str, jstatus: JobStatus = JobStatus.COMPLETED) -> JobResult:
    return JobResult(entity_type=entity, status=jstatus)


@pytest.mark.asyncio
async def test_invalidates_fighters_prefix_on_fighter_sync(_memory_cache: MemoryCacheManager) -> None:
    cache = _memory_cache
    await cache.set("mma:api:fighters:list", {"items": []}, 300)
    await cache.set("mma:api:events:list", {"items": []}, 300)

    await invalidate_after_sync(SyncEventCtx(run_id="r", provider_slug="espn"), _result(jobs=[_job("fighter")]))

    assert await cache.get("mma:api:fighters:list") is None
    assert await cache.get("mma:api:events:list") is not None


@pytest.mark.asyncio
async def test_event_and_competition_sync_busts_events_prefix(_memory_cache: MemoryCacheManager) -> None:
    cache = _memory_cache
    await cache.set("mma:api:events:detail:abc", {"id": "abc"}, 300)
    await cache.set("mma:api:rankings:all", {"categories": []}, 300)

    await invalidate_after_sync(
        SyncEventCtx(run_id="r", provider_slug="espn"),
        _result(jobs=[_job("event"), _job("competition"), _job("broadcast")]),
    )

    assert await cache.get("mma:api:events:detail:abc") is None
    assert await cache.get("mma:api:rankings:all") is not None


@pytest.mark.asyncio
async def test_ranking_sync_busts_rankings_prefix(_memory_cache: MemoryCacheManager) -> None:
    cache = _memory_cache
    await cache.set("mma:api:rankings:mens", {"categories": []}, 600)

    await invalidate_after_sync(SyncEventCtx(run_id="r", provider_slug="espn"), _result(jobs=[_job("ranking")]))

    assert await cache.get("mma:api:rankings:mens") is None


@pytest.mark.asyncio
async def test_failed_run_does_not_invalidate(_memory_cache: MemoryCacheManager) -> None:
    cache = _memory_cache
    await cache.set("mma:api:fighters:list", {"items": []}, 300)

    await invalidate_after_sync(
        SyncEventCtx(run_id="r", provider_slug="espn"),
        _result(status=SyncStatus.FAILED, jobs=[_job("fighter")]),
    )

    assert await cache.get("mma:api:fighters:list") is not None


@pytest.mark.asyncio
async def test_failed_job_does_not_invalidate_its_entity(_memory_cache: MemoryCacheManager) -> None:
    cache = _memory_cache
    await cache.set("mma:api:fighters:list", {"items": []}, 300)

    await invalidate_after_sync(
        SyncEventCtx(run_id="r", provider_slug="espn"),
        _result(jobs=[_job("fighter", JobStatus.FAILED), _job("ranking")]),
    )

    assert await cache.get("mma:api:fighters:list") is not None
    assert await cache.get("mma:api:rankings:mens") is None


def test_prefix_mapping_known_entities() -> None:
    assert _prefixes_for("fighter") == {"mma:api:fighters"}
    assert _prefixes_for("ranking") == {"mma:api:rankings"}
    assert _prefixes_for("event") == {"mma:api:events"}
    assert _prefixes_for("statistic") == {"mma:api:fighters", "mma:api:events"}


def test_records_backfill_busts_fighters_prefix() -> None:
    """Records backfill writes fighter_records + record-fetch status rows,
    both surfacing in the fighters:detail profile (Phase D D5)."""
    assert _prefixes_for("records") == {"mma:api:fighters"}


def test_prefix_mapping_unknown_entity_is_empty() -> None:
    assert _prefixes_for("goblin") == set()
