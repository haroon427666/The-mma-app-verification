#!/usr/bin/env python3
"""
Production Scheduler Entry Point.

Starts the autonomous sync service with all scheduled jobs.

Usage:
    python scheduler.py                    # Start all scheduled jobs
    python scheduler.py --full             # Start + run full sync immediately
    python scheduler.py --entity fighter   # Start + sync a specific entity
    python scheduler.py --dashboard       # Start with scheduler dashboard
"""

import asyncio
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler")

BANNER = """
╔══════════════════════════════════════════════════╗
║     MMA Backend — Autonomous Sync Service        ║
║         Production Orchestrator v7               ║
╚══════════════════════════════════════════════════╝
"""


class SyncContext:
    """Dummy context — production would inject real DB, Redis, providers."""

    def __init__(self):
        self.db = None
        self.redis = None
        self.db_session_factory = None
        self.espn_provider = None
        self.tsdb_provider = None
        self.octagon_provider = None

    def is_live_event_active(self) -> bool:
        return False


async def run_scheduler(do_full_sync: bool = False, entity: str | None = None):
    """Start the autonomous sync scheduler."""
    print(BANNER)

    # Initialize context (production: real DB, Redis, providers)
    ctx = SyncContext()

    # Create and start the manager
    manager = SyncManager(ctx)

    # Handle graceful shutdown
    loop = asyncio.get_running_loop()

    def _shutdown():
        logger.info("Received shutdown signal")
        asyncio.create_task(manager.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            pass  # Windows doesn't support add_signal_handler

    await manager.start()

    # Optional: trigger immediate sync
    if do_full_sync:
        run_id = await manager.trigger_full_sync()
        logger.info(f"Full sync triggered: {run_id}")
    elif entity:
        run_id = await manager.trigger_entity_sync(entity)
        logger.info(f"Entity sync triggered: {run_id}")

    logger.info("Scheduler running — press Ctrl+C to stop")

    # Keep running until shutdown
    try:
        while manager._running:
            await asyncio.sleep(5)
            status = await manager.get_status()
            # Print health summary every 60 seconds
    except asyncio.CancelledError:
        pass

    logger.info("Scheduler stopped")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MMA Backend — Autonomous Sync Service")
    parser.add_argument("--full", action="store_true", help="Run full sync on startup")
    parser.add_argument("--entity", help="Sync specific entity on startup")
    parser.add_argument("--dashboard", action="store_true", help="Start with dashboard mode")

    args = parser.parse_args()

    if args.dashboard:
        logger.info("Dashboard mode — use GET /scheduler/status for live view")

    try:
        asyncio.run(run_scheduler(do_full_sync=args.full, entity=args.entity))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
