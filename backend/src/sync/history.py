"""Sync History — records every sync run and per-entity job.

Tracks: started_at, completed_at, duration, provider, entity,
records created/updated/skipped/errored, API calls made.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SyncHistoryRecorder:
    """Records sync run and job history."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._active_run_id: str | None = None

    async def start_run(self, mode: str, provider: str | None = None) -> str:
        """Begin a new sync run. Returns run ID."""
        from sqlalchemy.dialects.postgresql import insert

        from src.db.base import new_uuid
        from src.db.models.support import SyncRun

        run_id = new_uuid()
        values: dict[str, Any] = {
            "id": run_id,
            "status": "RUNNING",
            "mode": mode,
            "provider": provider,
            "started_at": datetime.now(UTC),
        }

        await self._session.execute(insert(SyncRun).values(**values))
        await self._session.flush()
        self._active_run_id = run_id
        logger.info(f"Sync run {run_id[:8]} started: mode={mode}")
        return run_id

    async def record_job(
        self,
        entity_type: str,
        status: str = "PENDING",
        **metrics: Any,
    ) -> str:
        """Record a per-entity job within the active run."""
        from sqlalchemy.dialects.postgresql import insert

        from src.db.base import new_uuid
        from src.db.models.support import SyncJob

        if self._active_run_id is None:
            raise RuntimeError("No active sync run")

        job_id = new_uuid()
        values = {
            "id": job_id,
            "sync_run_id": self._active_run_id,
            "entity_type": entity_type,
            "status": status,
            **{k: v for k, v in metrics.items()
               if k in ("records_inserted", "records_updated", "records_skipped",
                        "records_errors", "api_calls", "duration_ms")},
        }

        await self._session.execute(insert(SyncJob).values(**values))
        await self._session.flush()
        return job_id

    async def complete_job(self, job_id: str, error: str | None = None) -> None:
        """Mark a job as completed or failed."""
        from sqlalchemy import update

        from src.db.models.support import SyncJob

        values = {
            "completed_at": datetime.now(UTC),
            "status": "FAILED" if error else "COMPLETED",
        }
        if error:
            values["error"] = error

        await self._session.execute(
            update(SyncJob).where(SyncJob.id == job_id).values(**values)
        )

    async def complete_run(
        self,
        total_inserted: int = 0,
        total_updated: int = 0,
        total_skipped: int = 0,
        total_errors: int = 0,
        api_calls: int = 0,
        duration_ms: float = 0.0,
        error: str | None = None,
    ) -> None:
        """Complete the active sync run."""
        from sqlalchemy import update

        from src.db.models.support import SyncRun

        if self._active_run_id is None:
            return

        values = {
            "completed_at": datetime.now(UTC),
            "status": "FAILED" if error else "COMPLETED",
            "total_inserted": total_inserted,
            "total_updated": total_updated,
            "total_skipped": total_skipped,
            "total_errors": total_errors,
            "api_calls": api_calls,
            "duration_ms": duration_ms,
        }
        if error:
            values["error"] = error

        await self._session.execute(
            update(SyncRun).where(SyncRun.id == self._active_run_id).values(**values)
        )
        logger.info(
            f"Sync run {self._active_run_id[:8]} completed: "
            f"{total_inserted} inserted, {total_updated} updated, "
            f"{total_errors} errors, {duration_ms:.0f}ms"
        )
        self._active_run_id = None
