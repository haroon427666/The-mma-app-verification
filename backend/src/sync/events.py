"""
Sync events — hook system for notifications, audit logs, tracing, WebSockets.

Every significant lifecycle event fires a hook. Subscribers (notifications,
metrics exporters, audit logs, WebSocket broadcasters) register handlers.

Usage:
    events = SyncEventBus()
    events.on_before_job(lambda ctx, job: logger.info(f"Starting {job.name}"))
    events.on_after_job(lambda ctx, job, result: metrics.push(result))
    events.on_failure(lambda ctx, job, error: slack.alert(error))
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from src.sync.types import EntityType

logger = logging.getLogger(__name__)


# ── Event types ───────────────────────────────────────────────────────────────
# Each handler receives (ctx, **kwargs) and returns None.
# Handlers are async — they run concurrently after the main operation completes.

BeforeSyncHandler = Callable[["SyncEventCtx"], Awaitable[None]]
AfterSyncHandler = Callable[["SyncEventCtx", "SyncResult"], Awaitable[None]]
BeforeJobHandler = Callable[["SyncEventCtx", EntityType], Awaitable[None]]
AfterJobHandler = Callable[["SyncEventCtx", EntityType, "JobResult"], Awaitable[None]]
OnFailureHandler = Callable[["SyncEventCtx", EntityType, Exception], Awaitable[None]]
OnRetryHandler = Callable[["SyncEventCtx", EntityType, int, Exception], Awaitable[None]]
OnBatchCompleteHandler = Callable[["SyncEventCtx", EntityType, int, int], Awaitable[None]]


# ── Lightweight event context ─────────────────────────────────────────────────
# A read-only snapshot of sync state at the time the event fired.
# Deliberately NOT the full SyncContext — handlers should not mutate sync state.


@dataclass(frozen=True)
class SyncEventCtx:
    """Read-only context snapshot passed to event handlers."""

    run_id: str
    provider_slug: str
    progress_pct: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


# ── Event Bus ─────────────────────────────────────────────────────────────────


@dataclass
class SyncEventBus:
    """In-process event bus for sync lifecycle events.

    Handlers run concurrently, fire-and-forget (don't block the sync pipeline).
    Failures in handlers are logged but never propagate to the sync engine.
    """

    # Sync-level hooks
    _before_sync: list[BeforeSyncHandler] = field(default_factory=list)
    _after_sync: list[AfterSyncHandler] = field(default_factory=list)

    # Job-level hooks
    _before_job: list[BeforeJobHandler] = field(default_factory=list)
    _after_job: list[AfterJobHandler] = field(default_factory=list)

    # Error hooks
    _on_failure: list[OnFailureHandler] = field(default_factory=list)
    _on_retry: list[OnRetryHandler] = field(default_factory=list)

    # Progress hooks
    _on_batch_complete: list[OnBatchCompleteHandler] = field(default_factory=list)

    # ── Registration ───────────────────────────────────────────────────────

    def on_before_sync(self, handler: BeforeSyncHandler) -> None:
        self._before_sync.append(handler)

    def on_after_sync(self, handler: AfterSyncHandler) -> None:
        self._after_sync.append(handler)

    def on_before_job(self, handler: BeforeJobHandler) -> None:
        self._before_job.append(handler)

    def on_after_job(self, handler: AfterJobHandler) -> None:
        self._after_job.append(handler)

    def on_failure(self, handler: OnFailureHandler) -> None:
        self._on_failure.append(handler)

    def on_retry(self, handler: OnRetryHandler) -> None:
        self._on_retry.append(handler)

    def on_batch_complete(self, handler: OnBatchCompleteHandler) -> None:
        self._on_batch_complete.append(handler)

    # ── Fire hooks ─────────────────────────────────────────────────────────

    async def fire_before_sync(self, ctx: SyncEventCtx) -> None:
        await self._fire(self._before_sync, ctx)

    async def fire_after_sync(self, ctx: SyncEventCtx, result: "SyncResult") -> None:
        await self._fire(self._after_sync, ctx, result)

    async def fire_before_job(self, ctx: SyncEventCtx, entity: EntityType) -> None:
        await self._fire(self._before_job, ctx, entity)

    async def fire_after_job(
        self, ctx: SyncEventCtx, entity: EntityType, result: "JobResult"
    ) -> None:
        await self._fire(self._after_job, ctx, entity, result)

    async def fire_failure(
        self, ctx: SyncEventCtx, entity: EntityType, error: Exception
    ) -> None:
        await self._fire(self._on_failure, ctx, entity, error)

    async def fire_retry(
        self, ctx: SyncEventCtx, entity: EntityType, attempt: int, error: Exception
    ) -> None:
        await self._fire(self._on_retry, ctx, entity, attempt, error)

    async def fire_batch_complete(
        self, ctx: SyncEventCtx, entity: EntityType, batch_num: int, items: int
    ) -> None:
        await self._fire(self._on_batch_complete, ctx, entity, batch_num, items)

    # ── Internal ───────────────────────────────────────────────────────────

    async def _fire(self, handlers: list, *args: Any) -> None:
        """Fire all handlers concurrently. Failures are logged, never raised."""
        if not handlers:
            return
        tasks = []
        for handler in handlers:
            tasks.append(asyncio.create_task(self._safe_call(handler, *args)))
        await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def _safe_call(handler: Callable, *args: Any) -> None:
        try:
            await handler(*args)
        except Exception:
            logger.exception("Sync event handler failed")


# ── Forward references ────────────────────────────────────────────────────────
# Avoid circular imports — resolved at runtime.
from src.sync.result import SyncResult  # noqa: E402
from src.sync.job import JobResult      # noqa: E402
