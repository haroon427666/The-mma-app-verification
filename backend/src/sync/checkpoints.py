"""Checkpoint Manager — persist and resume sync progress.

Stores per-entity + per-provider checkpoints so interrupted syncs
can resume without losing progress or creating duplicates.

Two managers, one abstraction:
- CheckpointManager          → sync_checkpoints (per-entity SyncState resume)
- DiscoveryCheckpointManager → sync_discovery_checkpoints (per-source walk resume)
"""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

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
    data: dict[str, Any] | None = None
    """Serialized SyncState payload (checkpoint dict, timestamps, cursors)."""


class CheckpointManager:
    """Persists and loads sync checkpoints."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, checkpoint: Checkpoint, data: dict[str, Any] | None = None) -> None:
        """Upsert a checkpoint.

        ``data`` is optional: when None the ``data`` column is left untouched
        (backward compatible with callers that don't use SyncState payloads).
        """
        from sqlalchemy.dialects.postgresql import insert

        from src.db.models.support import SyncCheckpoint

        values: dict[str, Any] = {
            "entity_type": checkpoint.entity_type,
            "provider": checkpoint.provider,
            "last_offset": checkpoint.last_offset,
            "last_page": checkpoint.last_page,
            "total_records": checkpoint.total_records,
            "status": checkpoint.status,
            "last_error": checkpoint.last_error,
            "completed": checkpoint.completed,
        }
        if data is not None:
            values["data"] = data

        # index_elements (not constraint=) is portable: Postgres renders
        # ON CONFLICT (entity_type, provider); SQLite renders the same column
        # list, which matches the unique constraint/index on both dialects.
        stmt = (
            insert(SyncCheckpoint)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["entity_type", "provider"],
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
            data=_normalize_data(row.data),
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


# ── Discovery-walk checkpoints (per-source resumable census) ───────────────


@dataclass
class DiscoveryCheckpoint:
    provider: str
    source: str
    league_slug: str = ""
    page: int = 0
    offset: int = 0
    discovered_count: int = 0
    last_athlete_id: str | None = None
    status: str = "IN_PROGRESS"
    last_error: str | None = None
    completed: bool = False
    run_id: str | None = None


class DiscoveryCheckpointManager:
    """Persists and loads per-source discovery-walk checkpoints.

    Same shape as CheckpointManager (one abstraction, second table): the
    fighter census walk saves progress after every page so a killed run
    resumes from the next page instead of re-enumerating from page 1.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, checkpoint: DiscoveryCheckpoint) -> None:
        """Upsert a discovery-walk checkpoint (unique provider/source/league)."""
        from sqlalchemy.dialects.postgresql import insert

        from src.db.models.support import SyncDiscoveryCheckpoint

        values: dict[str, Any] = {
            "provider": checkpoint.provider,
            "source": checkpoint.source,
            "league_slug": checkpoint.league_slug,
            "page": checkpoint.page,
            "offset": checkpoint.offset,
            "discovered_count": checkpoint.discovered_count,
            "last_athlete_id": checkpoint.last_athlete_id,
            "status": checkpoint.status,
            "last_error": checkpoint.last_error,
            "completed": checkpoint.completed,
            "run_id": checkpoint.run_id,
            "last_processed_at": datetime.now(UTC),
        }
        stmt = (
            insert(SyncDiscoveryCheckpoint)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["provider", "source", "league_slug"],
                set_=values,
            )
        )
        await self._session.execute(stmt)

    async def load(
        self, provider: str, source: str, league_slug: str = ""
    ) -> DiscoveryCheckpoint | None:
        """Load the last walk checkpoint for a provider/source/league."""
        from sqlalchemy import select

        from src.db.models.support import SyncDiscoveryCheckpoint

        result = await self._session.execute(
            select(SyncDiscoveryCheckpoint).where(
                SyncDiscoveryCheckpoint.provider == provider,
                SyncDiscoveryCheckpoint.source == source,
                SyncDiscoveryCheckpoint.league_slug == league_slug,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return DiscoveryCheckpoint(
            provider=row.provider,
            source=row.source,
            league_slug=row.league_slug,
            page=row.page,
            offset=row.offset,
            discovered_count=row.discovered_count,
            last_athlete_id=row.last_athlete_id,
            status=row.status,
            last_error=row.last_error,
            completed=row.completed,
            run_id=row.run_id,
        )


def _normalize_data(value: Any) -> dict[str, Any] | None:
    """SQLAlchemy JSON columns return dicts on Postgres; SQLite (tests) may
    return a JSON string. Normalize both to dict."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except (TypeError, ValueError):
            return None
    return None
