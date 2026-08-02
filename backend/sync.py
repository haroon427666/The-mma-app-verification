#!/usr/bin/env python3
""" 
MMA Backend — Production Sync Entry Point.

One command to populate the database from all three providers.

Usage:
    python sync.py --full                     # Full sync, all providers, all entities
    python sync.py --full --provider espn    # ESPN only
    python sync.py --resume                   # Resume from last checkpoint
    python sync.py --entity fighter           # Sync only fighters
    python sync.py --weekly                   # Enrichment-only sync (TSDB + Octagon)
    python sync.py --rankings                  # Rankings-only sync + verification

At the end of a successful run, your database contains:
    - All promotions (UFC, Bellator, PFL)
    - All fighters (1,809 from ESPN + enrichment from TSDB/Octagon)
    - All events (upcoming + past with embedded competitions)
    - All competitions (fight cards with results)
    - 24 ranking categories (full positional rankings)
    - Career records (all breakdowns: KO, submission, title fights)
    - Career statistics (striking, grappling, general)
    - Broadcast information
    - Venues with coordinates
    - Weight classes with boundaries
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime, timezone

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
║   ESPN (primary) + TheSportsDB + Octagon API     ║
╚══════════════════════════════════════════════════╝
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="MMA Backend — Production Sync Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync.py --full                    Full sync, all entities
  python sync.py --full --provider espn   ESPN only
  python sync.py --resume                  Resume from last checkpoint
  python sync.py --entity fighter          Fighters only
  python sync.py --weekly                  Enrichment sync (TSDB + Octagon)
  python sync.py --rankings                Rankings sync + Octagon verification
        """,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="Full sync from scratch")
    mode.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    mode.add_argument("--weekly", action="store_true", help="Enrichment sync only")
    mode.add_argument("--rankings", action="store_true", help="Rankings sync + verification")

    parser.add_argument("--provider", default="espn", help="Provider: espn, tsdb, octagon, all")
    parser.add_argument("--entity", help="Specific entity: fighter, event, competition, ranking, etc.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced, don't execute")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    return parser.parse_args()


async def setup_database():
    """Create database engine and run pending migrations."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from src.config import settings

    engine = create_async_engine(settings.database_url, echo=False)

    # Verify connectivity
    async with engine.connect() as conn:
        from sqlalchemy import text
        await conn.execute(text("SELECT 1"))
        logger.info("Database connected")

    return engine


async def setup_providers():
    """Initialize all three providers."""
    from src.providers.espn import ESPNProvider, ESPNClientConfig
    from src.providers.tsdb import TSDBProvider
    from src.providers.octagon import OctagonProvider

    espn = ESPNProvider(ESPNClientConfig())
    tsdb = TSDBProvider()
    octagon = OctagonProvider()

    await espn._ensure_started()
    await tsdb._ensure_started()
    await octagon._ensure_started()

    logger.info("All providers initialized: ESPN, TheSportsDB, Octagon API")
    return {"espn": espn, "tsdb": tsdb, "octagon": octagon}


async def close_providers(providers: dict):
    """Clean up provider connections."""
    for name, p in providers.items():
        try:
            await p.close()
        except Exception:
            pass
    logger.info("All providers closed")


async def run_full_sync(db_engine, providers: dict, entity_filter: str | None = None):
    """Run a complete sync: ESPN (primary) → Octagon (enrichment) → TSDB (enrichment)."""
    from src.sync.engine import SyncEngine
    from src.sync.pipeline import SyncPipeline
    from src.sync.context import SyncContext
    from src.sync.plan import SyncPlan
    from src.sync.types import EntityType

    # Build sync plan
    if entity_filter:
        entity_types = [EntityType(entity_filter)]
    else:
        entity_types = [
            EntityType.PROMOTION,
            EntityType.WEIGHT_CLASS,
            EntityType.VENUE,
            EntityType.FIGHTER,
            EntityType.EVENT,
            EntityType.COMPETITION,
            EntityType.RANKING,
            EntityType.STATISTIC,
            EntityType.BROADCAST,
        ]

    plan = SyncPlan(entity_types=entity_types, mode="full")
    context = SyncContext(db=db_engine, espn_provider=providers["espn"])

    engine = SyncEngine(context=context)
    pipeline = SyncPipeline(engine=engine)

    start = time.monotonic()
    logger.info(f"Starting FULL sync: {len(entity_types)} entities")

    result = await pipeline.execute(plan)

    elapsed = time.monotonic() - start
    logger.info(f"Sync completed in {elapsed:.1f}s")

    return result


async def run_enrichment_sync(db_engine, providers: dict):
    """Run enrichment-only sync: Octagon + TSDB media/bios."""
    from src.sync.engine import SyncEngine
    from src.sync.pipeline import SyncPipeline
    from src.sync.context import SyncContext
    from src.sync.plan import SyncPlan
    from src.sync.types import EntityType

    plan = SyncPlan(
        entity_types=[EntityType.FIGHTER],
        mode="enrichment",
        providers=["tsdb", "octagon"],
    )

    context = SyncContext(
        db=db_engine,
        espn_provider=providers["espn"],
        tsdb_provider=providers["tsdb"],
        octagon_provider=providers["octagon"],
    )

    pipeline = SyncPipeline(engine=SyncEngine(context=context))
    result = await pipeline.execute(plan)

    logger.info(f"Enrichment sync completed: {result}")
    return result


async def run_rankings_sync(db_engine, providers: dict):
    """Run rankings sync + Octagon verification."""
    from src.sync.engine import SyncEngine
    from src.sync.pipeline import SyncPipeline
    from src.sync.context import SyncContext
    from src.sync.plan import SyncPlan
    from src.sync.types import EntityType

    plan = SyncPlan(entity_types=[EntityType.RANKING], mode="full")

    context = SyncContext(
        db=db_engine,
        espn_provider=providers["espn"],
        octagon_provider=providers["octagon"],
    )

    pipeline = SyncPipeline(engine=SyncEngine(context=context))
    result = await pipeline.execute(plan)

    # Verify against Octagon
    if providers.get("octagon"):
        verification = await providers["octagon"].verify_rankings()
        logger.info(f"Rankings verification: {verification}")

    return result


def print_results(result):
    """Display sync results."""
    if result is None:
        return

    print("\n" + "=" * 60)
    print("SYNC RESULTS")
    print("=" * 60)

    if hasattr(result, "jobs"):
        for job_result in result.jobs:
            status = "✓" if not job_result.error else "✗"
            print(f"  {status} {job_result.entity_type:<20} "
                  f"inserted={job_result.records_inserted:<6} "
                  f"updated={job_result.records_updated:<6} "
                  f"skipped={job_result.records_skipped:<6} "
                  f"errors={job_result.records_errors:<6}"
                  f"{'  ERROR: ' + job_result.error if job_result.error else ''}")

    total_inserted = sum(j.records_inserted for j in result.jobs) if hasattr(result, "jobs") else 0
    total_updated = sum(j.records_updated for j in result.jobs) if hasattr(result, "jobs") else 0
    total_errors = sum(j.records_errors for j in result.jobs) if hasattr(result, "jobs") else 0

    print(f"\n  Total: {total_inserted} inserted, {total_updated} updated, {total_errors} errors")
    print("=" * 60)


async def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print(BANNER)
    logger.info(f"Mode: {'FULL' if args.full else 'RESUME' if args.resume else 'WEEKLY' if args.weekly else 'RANKINGS'}")
    logger.info(f"Provider: {args.provider}")

    if args.dry_run:
        logger.info("DRY RUN — no data will be written")
        return

    # Setup
    db_engine = await setup_database()
    providers = await setup_providers()

    try:
        if args.full:
            result = await run_full_sync(db_engine, providers, entity_filter=args.entity)
        elif args.rankings:
            result = await run_rankings_sync(db_engine, providers)
        elif args.weekly:
            result = await run_enrichment_sync(db_engine, providers)
        elif args.resume:
            logger.info("Resume mode — would pick up from last checkpoint")
            result = await run_full_sync(db_engine, providers, entity_filter=args.entity)
        else:
            logger.info("No mode specified. Use --full, --resume, --weekly, or --rankings.")
            result = None

        print_results(result)

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await close_providers(providers)
        await db_engine.dispose()

    logger.info("Sync engine shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
