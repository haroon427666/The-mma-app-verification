"""
Sync job — abstract base with rich metadata.

Every sync job exposes:
- entity_type: EntityType enum (never a magic string)
- depends_on: list[EntityType] that must complete first
- critical: abort entire run if this job fails
- batch_size: items per DB write batch
- supports_incremental: can do incremental sync

Jobs only implement:
- _fetch(ctx, state) → list[DTO]
- _transform(ctx, dtos) → list[DTO]  (optional, default pass-through)
- _upsert(ctx, dtos) → dict

Pipeline handles: retries, batching, pagination, cancellation, metrics, checkpointing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.sync.context import SyncContext
from src.sync.state import SyncState
from src.sync.types import EntityType, JobStatus

# ── Job Result ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class JobResult:
    """Immutable outcome of one sync job."""

    entity_type: str
    status: JobStatus
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_errors: int = 0
    api_calls: int = 0
    duration_ms: float = 0.0
    error_msg: str | None = None


# ── Abstract Sync Job ─────────────────────────────────────────────────────────


class SyncJob(ABC):
    """Abstract base for every sync job.

    Subclasses define metadata as class attributes and implement
    _fetch() and _upsert(). The SyncPipeline handles everything else.

    Example:
        class FighterSyncJob(SyncJob):
            entity_type = EntityType.FIGHTER
            depends_on = [EntityType.WEIGHT_CLASS, EntityType.PROMOTION]
            critical = True
            batch_size = 250
            supports_incremental = True

            async def _fetch(self, ctx, state):
                return await ctx.provider.fetch_fighters()

            async def _upsert(self, ctx, dtos):
                return await fighter_upsert.upsert_batch(ctx, dtos)
    """

    # ── Metadata (override in subclasses) ──────────────────────────────────

    entity_type: EntityType = NotImplemented
    """Which entity this job syncs."""

    depends_on: list[EntityType] = []
    """Entity types that must complete before this job can run."""

    critical: bool = True
    """If True, abort the entire sync run on failure."""

    batch_size: int = 500
    """Number of DTOs per database write batch."""

    supports_incremental: bool = False
    """If True, the pipeline uses SyncState for delta sync."""

    # ── Abstract methods (subclasses MUST implement) ───────────────────────

    @abstractmethod
    async def _fetch(
        self, ctx: SyncContext, state: SyncState
    ) -> list[Any]:
        """Fetch DTOs from the provider.

        Args:
            ctx: SyncContext with provider, db, logger, clock, metrics.
            state: Per-entity sync state (checkpoint, last sync, cursor).
                   Use state.last_cursor for pagination continuation.
                   Use state.updated_since for incremental delta.

        Returns:
            List of provider DTOs.
        """
        ...

    @abstractmethod
    async def _upsert(
        self, ctx: SyncContext, dtos: list[Any]
    ) -> dict[str, int]:
        """Write DTOs to the database.

        Args:
            ctx: SyncContext with db session.
            dtos: Batch of provider DTOs to upsert.

        Returns:
            dict with keys: inserted, updated, skipped, errors.
        """
        ...

    # ── Optional overrides ─────────────────────────────────────────────────

    async def _transform(
        self, ctx: SyncContext, dtos: list[Any]
    ) -> list[Any]:
        """Transform DTOs before upsert. Default: pass-through.

        Override to normalize data, filter, enrich, or validate.
        """
        return dtos

    # ── Convenience properties ─────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Human-readable job name."""
        return self.entity_type.value
