"""Checkpoint Manager — persist and resume sync progress.

Stores per-entity + per-provider checkpoints so interrupted syncs
can resume without losing progress or creating duplicates.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    entity_type: str
    provider: str
    last_offset: int = 0
    last_page: int = 0
    total_records: int = 0
    status: str = "IN_PROGRESS"
    last_error: str | None = None
    completed: bool = False


class CheckpointManager:
    """Persists and loads sync checkpoints."""

    def __init__(self, session):
        self._session = session

    async def save(self, checkpoint: Checkpoint) -> None:
        """Upsert a checkpoint."""
        from sqlalchemy.dialects.postgresql import insert
        from src.db.models.support import SyncCheckpoint

        values = {
            "entity_type": checkpoint.entity_type,
            "provider": checkpoint.provider,
            "last_offset": checkpoint.last_offset,
            "last_page": checkpoint.last_page,
            "total_records": checkpoint.total_records,
            "status": checkpoint.status,
            "last_error": checkpoint.last_error,
            "completed": checkpoint.completed,
        }

        stmt = (
            insert(SyncCheckpoint)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_sync_checkpoints_entity_provider",
                set_=values,
            )
        )
        await self._session.execute(stmt)
        logger.debug(
            f"Checkpoint saved: {checkpoint.entity_type}/{checkpoint.provider} "
            f"offset={checkpoint.last_offset}"
        )

    async def load(
        self, entity_type: str, provider: str
    ) -> Checkpoint | None:
        """Load the last checkpoint for an entity+provider."""
        from sqlalchemy import select
        from src.db.models.support import SyncCheckpoint

        result = await self._session.execute(
            select(SyncCheckpoint).where(
                SyncCheckpoint.entity_type == entity_type,
                SyncCheckpoint.provider == provider,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return Checkpoint(
            entity_type=row.entity_type,
            provider=row.provider,
            last_offset=row.last_offset,
            last_page=row.last_page,
            total_records=row.total_records,
            status=row.status,
            last_error=row.last_error,
            completed=row.completed,
        )

    async def mark_completed(self, entity_type: str, provider: str) -> None:
        """Mark a checkpoint as finished."""
        from sqlalchemy import update
        from src.db.models.support import SyncCheckpoint

        await self._session.execute(
            update(SyncCheckpoint)
            .where(
                SyncCheckpoint.entity_type == entity_type,
                SyncCheckpoint.provider == provider,
            )
            .values(completed=True, status="COMPLETED")
        )

    async def mark_failed(
        self, entity_type: str, provider: str, error: str,
    ) -> None:
        """Mark a checkpoint as failed (will resume from last offset)."""
        from sqlalchemy import update
        from src.db.models.support import SyncCheckpoint

        await self._session.execute(
            update(SyncCheckpoint)
            .where(
                SyncCheckpoint.entity_type == entity_type,
                SyncCheckpoint.provider == provider,
            )
            .values(status="FAILED", last_error=error, completed=False)
        )
