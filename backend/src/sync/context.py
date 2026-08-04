"""
Sync context — immutable dependency bag for a single sync run.

Every sync operation receives this context. No global state, no singletons.
Provider-agnostic: the provider field is BaseDataProvider, never ESPN.

IMPORTANT: Never call datetime.now() or time.monotonic() directly in sync code.
Use ctx.clock instead. Testing becomes trivial with FrozenClock.
"""

import uuid
from dataclasses import dataclass, field
from logging import Logger

from sqlalchemy.ext.asyncio import AsyncSession

from src.providers.base import BaseDataProvider
from src.sync.clock import Clock, SystemClock
from src.sync.metrics import SyncMetrics
from src.sync.types import SyncSchemaVersion

# ── Cancellation ──────────────────────────────────────────────────────────────


class CancelledError(Exception):
    """Raised when a sync operation is cancelled mid-execution."""


@dataclass
class CancellationToken:
    """Signal for graceful shutdown of long-running sync operations."""

    is_cancelled: bool = False
    cancel_reason: str | None = None

    def cancel(self, reason: str = "manual cancellation") -> None:
        self.is_cancelled = True
        self.cancel_reason = reason

    def check(self) -> None:
        if self.is_cancelled:
            raise CancelledError(self.cancel_reason or "Sync cancelled")


# ── Progress ──────────────────────────────────────────────────────────────────


@dataclass
class ProgressTracker:
    """Monotonic progress tracker for a single sync run."""

    total_jobs: int = 0
    completed_jobs: int = 0
    current_entity: str = ""
    current_page: int = 0
    items_processed: int = 0

    def set_total(self, total: int) -> None:
        self.total_jobs = total

    def set_current(self, entity_type: str) -> None:
        self.current_entity = entity_type
        self.current_page = 0
        self.items_processed = 0

    def advance(self, items: int, page: int) -> None:
        self.items_processed += items
        self.current_page = page

    def mark_completed(self, _entity_type: str) -> None:
        self.completed_jobs += 1
        self.current_entity = ""
        self.current_page = 0
        self.items_processed = 0

    @property
    def percent(self) -> float:
        if self.total_jobs == 0:
            return 0.0
        return round(self.completed_jobs / self.total_jobs * 100, 1)


# ── Sync Context ───────────────────────────────────────────────────────────────


@dataclass
class SyncContext:
    """Immutable dependency bag for a single sync run.

    Fields:
        run_id: Unique UUID for this run.
        provider: Data source — injected BaseDataProvider, never hardcoded.
        db: SQLAlchemy async session.
        logger: Structured logger with run_id bound.
        clock: Injectable time source (SystemClock in prod, FrozenClock in tests).
        metrics: Strongly-typed metrics accumulator.
        token: Cancellation signal.
        progress: Monotonic progress tracker.
        schema_version: Provider schema version for conditional transforms.
    """

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider: BaseDataProvider | None = None
    db: AsyncSession | None = None
    logger: Logger | None = None
    clock: Clock = field(default_factory=SystemClock)
    metrics: SyncMetrics = field(default_factory=SyncMetrics)
    token: CancellationToken = field(default_factory=CancellationToken)
    progress: ProgressTracker = field(default_factory=ProgressTracker)
    schema_version: SyncSchemaVersion | None = None
