#!/usr/bin/env python3
""" 
MMA Backend — Production Sync Entry Point.

One command to populate the database from the ESPN provider
through the real sync engine (SyncEngine → SyncPipeline → SyncJob).

Usage:
    python sync.py --full                     # Full sync (all 9 entity types)
    python sync.py --full --provider espn    # ESPN only (default)
    python sync.py --resume                   # Resume from last checkpoint
    python sync.py --entity fighter           # Sync only fighters
    python sync.py --weekly                   # Fighters + statistics (closest weekly run)
    python sync.py --rankings                 # Rankings-only sync

At the end of a successful run, your database contains:
    - All promotions (UFC, Bellator, PFL)
    - All fighters (from ESPN)
    - All events (upcoming + past with embedded competitions)
    - All competitions (fight cards with results)
    - Ranking categories (positional rankings)
    - Career statistics (striking, grappling, general)
    - Broadcast information
    - Venues with coordinates
    - Weight classes with boundaries

NOTE: TSDB + Octagon enrichment providers are deferred — the engine job
registry currently contains the 9 ESPN jobs only.
"""

import argparse
import asyncio
import logging
import sys

from sqlalchemy.ext.asyncio import AsyncSession

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sync")

# ── Banner ─────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════╗
║           MMA Backend — Sync Engine              ║
║   ESPN (primary) via SyncEngine + SyncPipeline   ║
╚══════════════════════════════════════════════════╝
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="MMA Backend — Production Sync Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync.py --full                    Full sync, all entities
  python sync.py --full --provider espn   ESPN only (default)
  python sync.py --resume                  Resume from last checkpoint
  python sync.py --entity fighter          Fighters only
  python sync.py --weekly                  Fighters + statistics
  python sync.py --rankings                Rankings sync
        """,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="Full sync from scratch")
    mode.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    mode.add_argument("--weekly", action="store_true", help="Fighters + statistics run")
    mode.add_argument("--rankings", action="store_true", help="Rankings sync")

    parser.add_argument("--provider", default="espn", help="Provider: espn (default) or all")
    parser.add_argument("--entity", help="Specific entity: fighter, event, competition, ranking, etc.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced, don't execute")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    return parser.parse_args()


async def setup_database() -> AsyncSession:
    """Create database session and verify connectivity."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from src.config import settings

    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        logger.info("Database connected")

    session = AsyncSession(engine)
    return session


async def setup_providers():
    """Initialize the ESPN provider (the only provider wired to sync jobs)."""
    from src.providers.espn import ESPNClientConfig, ESPNProvider

    espn = ESPNProvider(ESPNClientConfig())
    await espn._ensure_started()
    logger.info("Provider initialized: ESPN")
    return {"espn": espn}


async def close_providers(providers: dict):
    """Clean up provider connections."""
    for p in providers.values():
        try:
            await p.close()
        except Exception:
            pass
    logger.info("All providers closed")


def build_engine(session: AsyncSession | None = None):
    """Build the real SyncEngine with all ESPN jobs.

    With a DB session the engine uses DatabaseSyncStateStore so checkpoints
    survive process restarts (crash-resume). Without one (tests, scheduler)
    it falls back to the in-memory store.
    """
    from src.providers.espn.jobs import (
        ESPN_BroadcastSyncJob,
        ESPN_CompetitionSyncJob,
        ESPN_EventSyncJob,
        ESPN_FighterSyncJob,
        ESPN_HistoricalEventSyncJob,
        ESPN_PromotionSyncJob,
        ESPN_RankingSyncJob,
        ESPN_RecordsBackfillJob,
        ESPN_StatisticSyncJob,
        ESPN_VenueSyncJob,
        ESPN_WeightClassSyncJob,
    )
    from src.sync.engine import SyncEngine
    from src.sync.state_store import DatabaseSyncStateStore, MemorySyncStateStore
    from src.sync.types import EntityType

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
        EntityType.RECORDS: ESPN_RecordsBackfillJob(),
        EntityType.HISTORICAL_EVENT: ESPN_HistoricalEventSyncJob(),
    }
    statestore = (
        DatabaseSyncStateStore(session)
        if session is not None
        else MemorySyncStateStore()
    )
    return SyncEngine(jobs=jobs, statestore=statestore)


def _build_plan(plan_name: str, entity_filter: str | None):
    """Return the SyncPlan for the requested mode + optional entity filter."""
    from src.sync.plan import (
        EventsPlan,
        FighterPlan,
        FoundationPlan,
        FullSyncPlan,
        RankingsPlan,
        SyncPlan,
    )
    from src.sync.types import EntityType

    if entity_filter:
        try:
            entity = EntityType(entity_filter)
        except ValueError:
            valid = ", ".join(e.value for e in EntityType)
            raise SystemExit(f"Unknown entity '{entity_filter}'. Valid: {valid}")
        return SyncPlan(
            name="single_sync",
            description=f"Single entity sync: {entity.value}",
            order=[entity],
        )

    if plan_name == "full":
        return FullSyncPlan()
    if plan_name == "rankings":
        return RankingsPlan()
    if plan_name == "events":
        return EventsPlan()
    if plan_name == "fighters":
        return FighterPlan()
    if plan_name == "foundation":
        return FoundationPlan()
    raise SystemExit(f"Unknown plan '{plan_name}'")


async def run_sync(
    session: AsyncSession,
    providers: dict,
    plan_name: str,
    entity_filter: str | None = None,
    mode: str | None = None,
):
    """Run a sync plan through the real engine, then commit the transaction."""
    from src.sync.types import SyncMode

    plan = _build_plan(plan_name, entity_filter)
    engine = build_engine(session)
    espn = providers["espn"]

    logger.info(
        f"Starting sync: plan={plan.name} jobs={plan.job_count} "
        f"mode={mode or 'auto'}"
    )

    result = await engine.execute(
        plan=plan,
        provider=espn,
        db_session=session,
        mode=SyncMode(mode) if mode else None,
    )

    await session.commit()
    logger.info(
        f"Sync finished: {result.overall_status.value} "
        f"inserted={result.total_inserted} updated={result.total_updated} "
        f"skipped={result.total_skipped} errors={result.total_errors} "
        f"duration={result.duration_ms:.0f}ms"
    )
    return result


def print_results(result):
    """Display sync results."""
    if result is None:
        return

    summary = result.summary()
    print("\n" + "=" * 60)
    print("SYNC RESULTS")
    print("=" * 60)
    for job in summary["jobs"]:
        mark = "✓" if job["status"] == "COMPLETED" else "✗"
        print(
            f"  {mark} {job['entity']:<20} "
            f"inserted={job['inserted']:<6} "
            f"updated={job['updated']:<6} "
            f"skipped={job['skipped']:<6} "
            f"errors={job['errors']:<6}"
            f"{'  ERROR: ' + job['error'] if job['error'] else ''}"
        )
    print(f"\n  Status: {summary['status']} | {summary['duration_ms']:.0f}ms")
    print(f"  Total: {summary['total_inserted']} inserted, "
          f"{summary['total_updated']} updated, {summary['total_errors']} errors")
    print("=" * 60)


async def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print(BANNER)
    logger.info(f"Mode: {'FULL' if args.full else 'RESUME' if args.resume else 'WEEKLY' if args.weekly else 'RANKINGS'}")
    logger.info(f"Provider: {args.provider}")

    if args.provider not in ("espn", "all"):
        raise SystemExit("Only 'espn' (default) and 'all' (= espn) are wired. TSDB/Octagon enrichment is deferred.")

    if args.dry_run:
        plan = _build_plan(
            "full" if args.full else "rankings" if args.rankings else "fighters" if args.weekly else "full",
            args.entity,
        )
        logger.info(f"DRY RUN — would execute plan '{plan.name}' ({plan.job_count} jobs)")
        return

    session = await setup_database()
    providers = await setup_providers()

    try:
        if args.full:
            result = await run_sync(session, providers, "full", entity_filter=args.entity)
        elif args.rankings:
            result = await run_sync(session, providers, "rankings")
        elif args.weekly:
            logger.info("Weekly run: fighters + statistics (TSDB/Octagon enrichment deferred)")
            result = await run_sync(session, providers, "fighters")
        elif args.resume:
            logger.info("Resume mode — engine resumes from last checkpoint")
            result = await run_sync(session, providers, "full", entity_filter=args.entity, mode="resume")
        else:
            logger.info("No mode specified. Use --full, --resume, --weekly, or --rankings.")
            result = None

        print_results(result)

    except Exception:
        logger.exception("Sync failed")
        sys.exit(1)
    finally:
        await close_providers(providers)
        await session.close()

    logger.info("Sync engine shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
