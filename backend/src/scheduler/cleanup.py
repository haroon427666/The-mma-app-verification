"""Maintenance Tasks — automatic cleanup of stale data.

Runs daily. Cleans up:
- Expired sync checkpoints (completed > 7 days ago)
- Old provider payloads (> 90 days)
- Completed dead letter entries (> 30 days)
- Old sync run history (> 30 days)
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

logger = logging.getLogger(__name__)


class MaintenanceCleanup:
    """Daily maintenance — keeps the database lean."""

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def run(self) -> dict[str, int]:
        """Run all cleanup tasks. Returns counts per task."""
        results = {}

        try:
            results["payloads_pruned"] = await self._prune_payloads()
        except Exception as e:
            logger.error(f"Payload prune failed: {e}")
            results["payloads_pruned"] = 0

        try:
            results["checkpoints_cleaned"] = await self._clean_checkpoints()
        except Exception as e:
            logger.error(f"Checkpoint cleanup failed: {e}")
            results["checkpoints_cleaned"] = 0

        try:
            results["dead_letters_archived"] = await self._archive_dead_letters()
        except Exception as e:
            logger.error(f"Dead letter archive failed: {e}")
            results["dead_letters_archived"] = 0

        try:
            results["sync_history_pruned"] = await self._prune_sync_history()
        except Exception as e:
            logger.error(f"Sync history prune failed: {e}")
            results["sync_history_pruned"] = 0

        logger.info(f"Cleanup complete: {results}")
        return results

    async def _prune_payloads(self) -> int:
        """Delete provider payloads older than 90 days."""
        cutoff = datetime.now(UTC) - timedelta(days=90)
        async with self._session_factory() as session:
            result = await session.execute(
                text("DELETE FROM provider_payloads WHERE fetched_at < :cutoff"),
                {"cutoff": cutoff},
            )
            await session.commit()
            count: int = result.rowcount
            if count:
                logger.info(f"Pruned {count} old payloads")
            return count

    async def _clean_checkpoints(self) -> int:
        """Delete completed checkpoints older than 7 days."""
        cutoff = datetime.now(UTC) - timedelta(days=7)
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    "DELETE FROM sync_checkpoints "
                    "WHERE completed = true AND updated_at < :cutoff"
                ),
                {"cutoff": cutoff},
            )
            await session.commit()
            count: int = result.rowcount
            return count

    async def _archive_dead_letters(self) -> int:
        """Delete replayed dead letters older than 30 days."""
        cutoff = datetime.now(UTC) - timedelta(days=30)
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    "DELETE FROM dead_letters "
                    "WHERE replayed = true AND created_at < :cutoff"
                ),
                {"cutoff": cutoff},
            )
            await session.commit()
            count: int = result.rowcount
            return count

    async def _prune_sync_history(self) -> int:
        """Keep only last 30 days of sync history."""
        cutoff = datetime.now(UTC) - timedelta(days=30)
        async with self._session_factory() as session:
            result = await session.execute(
                text("DELETE FROM sync_runs WHERE created_at < :cutoff"),
                {"cutoff": cutoff},
            )
            await session.commit()
            count: int = result.rowcount
            return count
