"""SchedulerContext — dependency bag passed to SyncManager at startup.

Provides everything the scheduler's jobs need: providers, a Redis client
(None-safe), a DB session factory, and live-event detection.

Wired in the FastAPI lifespan only when ``SYNC_ENABLED=true``.
"""

from dataclasses import dataclass
from typing import Any

from src.scheduler.live_mode import LiveModeDetector


@dataclass
class SchedulerContext:
    """Dependency bag for SyncManager.

    Attributes:
        redis: Shared Redis client, or None when Redis is not configured.
        db_session_factory: Async session factory for DB access.
        db: Read-only property yielding a fresh AsyncSession per access.
        espn_provider: ESPN data provider (started).
        tsdb_provider: TheSportsDB enrichment provider (started).
        octagon_provider: Octagon enrichment provider (started).
        live_detector: Live-event detector (db-backed).
    """

    redis: Any | None = None
    db_session_factory: Any = None
    espn_provider: Any = None
    tsdb_provider: Any = None
    octagon_provider: Any = None
    live_detector: LiveModeDetector | None = None

    @property
    def db(self) -> Any:
        """Fresh async session for job work (never shared across jobs)."""
        if self.db_session_factory is None:
            return None
        return self.db_session_factory()

    def is_live_event_active(self) -> bool:
        """Best-effort live-event check without hitting the DB."""
        if self.live_detector is not None:
            return self.live_detector.is_live
        return False


async def build_scheduler_context() -> SchedulerContext:
    """Construct the scheduler context with all providers started.

    Raises:
        RuntimeError: if a provider fails to start.
    """
    from src.db.session import async_session_factory
    from src.middleware.redis import get_redis
    from src.providers.espn import ESPNClientConfig, ESPNProvider
    from src.providers.octagon import OctagonProvider
    from src.providers.tsdb import TSDBProvider

    espn = ESPNProvider(ESPNClientConfig())
    tsdb = TSDBProvider()
    octagon = OctagonProvider()

    await espn._ensure_started()
    await tsdb._ensure_started()
    await octagon._ensure_started()
    return SchedulerContext(
        redis=get_redis(),
        db_session_factory=async_session_factory,
        espn_provider=espn,
        tsdb_provider=tsdb,
        octagon_provider=octagon,
        live_detector=LiveModeDetector(async_session_factory),
    )