"""Live Postgres sync acceptance test — env-gated.

Run with:  MMA_LIVE_SYNC=1 python -m pytest tests/integration/test_sync_live.py -v -s

Requires:
- A running Postgres reachable via settings.database_url with migrations
  applied (`alembic upgrade head`).
- ESPN network access (real provider).

Covers the ESPN integration acceptance surface:
- FullSyncPlan (all 10 entity types incl. historical-event discovery) lands
  real rows in every sync table.
- Run TWICE — the second run must be idempotent (no duplicate fighters/
  events/competitions; counts stable).
- DB integrity: no duplicate (provider, external_id) pairs, one
  fighter_records row per fighter, no orphaned sync_jobs.
"""

import os

import pytest

RUN_LIVE = os.environ.get("MMA_LIVE_SYNC") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason="set MMA_LIVE_SYNC=1 to run the live Postgres sync acceptance test",
)

# Bounded run defaults (override via env if needed):
# - ESPN_MAX_PAGES caps every paginate() walk (global listing + rosters).
# - ESPN_FIGHTER_SYNC_LIMIT bounds the per-run fighter resolution window.
# - ESPN_MAX_HISTORICAL_EVENTS bounds the winningFight historical chain.
# - ESPN_STATS_MAX_FIGHTERS bounds career-stat enumeration.
# - ESPN_EVENTLOG_ENABLED + ESPN_EVENTLOG_MAX_FIGHTERS bound eventlog breadth.
BOUNDS = {
    "ESPN_MAX_PAGES": "25",
    "ESPN_FIGHTER_SYNC_LIMIT": "100",
    "ESPN_MAX_HISTORICAL_EVENTS": "5",
    "ESPN_STATS_MAX_FIGHTERS": "25",
    "ESPN_EVENTLOG_ENABLED": "1",
    "ESPN_EVENTLOG_MAX_FIGHTERS": "10",
}


@pytest.mark.asyncio
async def test_full_sync_populates_live_database_twice_idempotently():
    for key, value in BOUNDS.items():
        os.environ.setdefault(key, value)

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    from src.config import settings
    from src.providers.espn import ESPNClientConfig, ESPNProvider
    from src.providers.espn.jobs import (
        ESPN_BroadcastSyncJob,
        ESPN_CompetitionSyncJob,
        ESPN_EventSyncJob,
        ESPN_FighterSyncJob,
        ESPN_HistoricalEventSyncJob,
        ESPN_PromotionSyncJob,
        ESPN_RankingSyncJob,
        ESPN_StatisticSyncJob,
        ESPN_VenueSyncJob,
        ESPN_WeightClassSyncJob,
    )
    from src.sync.engine import SyncEngine
    from src.sync.plan import FullSyncPlan
    from src.sync.state_store import MemorySyncStateStore
    from src.sync.types import EntityType

    provider = ESPNProvider(ESPNClientConfig())
    await provider._ensure_started()

    jobs = {
        EntityType.PROMOTION: ESPN_PromotionSyncJob(),
        EntityType.VENUE: ESPN_VenueSyncJob(),
        EntityType.WEIGHT_CLASS: ESPN_WeightClassSyncJob(),
        EntityType.FIGHTER: ESPN_FighterSyncJob(),
        EntityType.EVENT: ESPN_EventSyncJob(),
        EntityType.COMPETITION: ESPN_CompetitionSyncJob(),
        EntityType.BROADCAST: ESPN_BroadcastSyncJob(),
        EntityType.STATISTIC: ESPN_StatisticSyncJob(),
        EntityType.RANKING: ESPN_RankingSyncJob(),
        EntityType.HISTORICAL_EVENT: ESPN_HistoricalEventSyncJob(),
    }
    engine = SyncEngine(jobs=jobs, statestore=MemorySyncStateStore())

    db_engine = create_async_engine(settings.database_url, echo=False)
    session = AsyncSession(db_engine)

    # Fresh slate for run 1 — this test owns the sync tables on the
    # acceptance DB. (TRUNCATE keeps run-1 counts attributable to this run.)
    truncate_tables = (
        "promotions, venues, weight_classes, fighters, fighter_records, "
        "events, competitions, competitors, broadcasts, statistics, rankings, "
        "external_ids, sync_runs, sync_jobs, sync_checkpoints, "
        "provider_payloads, provider_conflicts, dead_letters"
    )
    async with AsyncSession(db_engine) as clean_session:
        await clean_session.execute(text(f"TRUNCATE {truncate_tables} CASCADE"))
        await clean_session.commit()

    try:
        result1 = await engine.execute(
            plan=FullSyncPlan(), provider=provider, db_session=session
        )
        await session.commit()
        counts1 = await _row_counts(db_engine)

        # Run 2 — same engine, same in-memory checkpoint (ID set cached):
        # must be IDEMPOTENT — upserts, not inserts; no duplicates.
        result2 = await engine.execute(
            plan=FullSyncPlan(), provider=provider, db_session=session
        )
        await session.commit()
        counts2 = await _row_counts(db_engine)
    finally:
        await provider.close()
        await session.close()
        await db_engine.dispose()

    print("SYNC RUN 1:", result1.summary())
    print("SYNC RUN 2:", result2.summary())
    print("COUNTS RUN 1:", counts1)
    print("COUNTS RUN 2:", counts2)

    # ── Acceptance criterion (zaro-v5 C5) — run 1 landed real data ─────────
    assert counts1["promotions"] > 0, "no promotions synced"
    assert counts1["fighters"] > 0, "no fighters synced"
    assert counts1["events"] > 0, "no events synced"
    assert counts1["rankings"] > 0, "no rankings synced"
    assert counts1["sync_runs"] > 0, "no sync_runs record written"

    # ── ESPN integration surfaces exercised ────────────────────────────────
    assert counts1["sync_jobs"] > 0, "no sync_jobs records written"
    assert counts1["competitions"] > 0, "no competitions synced"
    assert counts1["competitors"] > 0, "no competitors synced"
    assert counts1["weight_classes"] > 0, "no weight classes synced"

    # Historical-event discovery ran as a job in the plan.
    async with AsyncSession(db_engine) as check:
        row = await check.execute(
            text("SELECT count(*) FROM sync_jobs WHERE entity_type = 'historical_event'")
        )
        assert int(row.scalar_one()) > 0, "historical_event job did not run"

    # ── Idempotency (run 2 must not multiply rows) ─────────────────────────
    for table in ("fighters", "events", "competitions", "competitors",
                  "fighter_records", "statistics", "rankings"):
        assert counts2[table] == counts1[table], (
            f"{table}: run 2 changed row count ({counts1[table]} → {counts2[table]})"
        )

    # ── DB integrity: no duplicate provider identities ─────────────────────
    async with AsyncSession(db_engine) as check:
        for table in ("fighters", "events", "competitions"):
            row = await check.execute(text(
                f"SELECT count(*) FROM (SELECT provider, external_id, count(*) "
                f"FROM {table} GROUP BY provider, external_id HAVING count(*) > 1) dup"
            ))
            assert int(row.scalar_one()) == 0, f"duplicate (provider, external_id) in {table}"

        # One fighter_records row per fighter (unique fighter_id)
        row = await check.execute(text(
            "SELECT count(*) FROM fighter_records fr "
            "JOIN (SELECT fighter_id, count(*) c FROM fighter_records GROUP BY fighter_id "
            "HAVING count(*) > 1) d ON d.fighter_id = fr.fighter_id"
        ))
        assert int(row.scalar_one()) == 0, "duplicate fighter_records rows"

        # No orphaned sync_jobs (every job belongs to a recorded run)
        row = await check.execute(text(
            "SELECT count(*) FROM sync_jobs sj "
            "LEFT JOIN sync_runs sr ON sr.id = sj.sync_run_id WHERE sr.id IS NULL"
        ))
        assert int(row.scalar_one()) == 0, "orphaned sync_jobs rows"


async def _row_counts(db_engine) -> dict[str, int]:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    tables = (
        "promotions", "venues", "weight_classes", "fighters", "fighter_records",
        "events", "competitions", "competitors", "broadcasts", "statistics",
        "rankings", "sync_runs", "sync_jobs",
    )
    counts: dict[str, int] = {}
    async with AsyncSession(db_engine) as session:
        for table in tables:
            try:
                row = await session.execute(text(f"SELECT count(*) FROM {table}"))
                counts[table] = int(row.scalar_one())
            except Exception as e:  # pragma: no cover - table missing
                counts[table] = -1
                print(f"count failed for {table}: {e}")
    return counts
