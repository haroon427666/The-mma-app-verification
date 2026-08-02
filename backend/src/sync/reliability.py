"""
Reliability layer — bundles circuit breaker, failure classification,
dead-letter queue, and event hooks into one injectable config.

Wired into SyncPipeline so every job inherits reliability behavior
without changing individual job implementations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from src.sync.dead_letter import DeadLetterQueue, DeadLetterRecord
from src.sync.events import SyncEventBus, SyncEventCtx
from src.sync.failure import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    FailureCategory,
    FailureClassifier,
)
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


# ── Reliability Config ────────────────────────────────────────────────────────


@dataclass
class ReliabilityConfig:
    """Bundled reliability components injected into SyncPipeline.

    Usage:
        reliability = ReliabilityConfig(
            circuit_breaker=CircuitBreaker(provider_slug="espn"),
            dead_letter=DeadLetterQueue(),
            events=SyncEventBus(),
        )
        pipeline = SyncPipeline(job=job, reliability=reliability)
    """

    circuit_breaker: CircuitBreaker | None = None
    """Per-provider circuit breaker. If None, no circuit breaking."""

    classifier: FailureClassifier = field(default_factory=FailureClassifier)
    """Classifies exceptions into failure categories."""

    dead_letter: DeadLetterQueue | None = None
    """Dead-letter queue for unrecoverable DTOs. If None, errors are logged only."""

    events: SyncEventBus | None = None
    """Event bus for reliability events (circuit open/close, dead letter)."""

    # ── High-level API ─────────────────────────────────────────────────────

    async def before_provider_call(self, provider_slug: str) -> None:
        """Check circuit breaker before a provider call.

        Raises CircuitBreakerOpenError if the circuit is open.
        """
        if self.circuit_breaker is None:
            return
        await self.circuit_breaker.before_call()

    async def on_provider_success(self) -> None:
        """Record a successful provider call."""
        if self.circuit_breaker is None:
            return
        self.circuit_breaker.on_success()
        if (
            self.events
            and self.circuit_breaker.state.value != "CLOSED"
        ):
            # Circuit just reset — fire event
            pass  # Fired by circuit breaker internals

    async def on_provider_failure(
        self,
        error: Exception,
        provider_slug: str,
        entity_type: EntityType | None = None,
        dto: Any | None = None,
        dto_external_id: str | None = None,
        run_id: str = "",
    ) -> FailureCategory:
        """Handle a provider failure: classify, circuit-break, dead-letter.

        Returns the failure category so the caller can decide next steps.
        """
        category = self.classifier.classify(error)

        # Circuit breaker: trip on TRANSIENT or PROVIDER_DOWN
        if self.circuit_breaker:
            self.circuit_breaker.on_failure(category)

        # Dead letter: store PERMANENT and DATA_ERROR DTOs
        if category in (FailureCategory.PERMANENT, FailureCategory.DATA_ERROR):
            if self.dead_letter and dto is not None and entity_type is not None:
                await self._dead_letter_dto(
                    entity_type=entity_type,
                    external_id=dto_external_id or "unknown",
                    provider_slug=provider_slug,
                    dto=dto,
                    error=error,
                    category=category,
                    run_id=run_id,
                )

        # Log
        if category == FailureCategory.TRANSIENT:
            logger.warning(f"[{provider_slug}] Transient failure: {error}")
        elif category == FailureCategory.PROVIDER_DOWN:
            logger.error(f"[{provider_slug}] Provider appears DOWN: {error}")
        elif category == FailureCategory.PERMANENT:
            logger.error(f"[{provider_slug}] Permanent failure (dead-lettered): {error}")
        elif category == FailureCategory.DATA_ERROR:
            logger.error(f"[{provider_slug}] Data error (dead-lettered): {error}")

        return category

    async def dead_letter_dto(
        self,
        entity_type: EntityType,
        external_id: str,
        provider_slug: str,
        dto: Any,
        error: Exception,
        run_id: str = "",
    ) -> None:
        """Explicitly dead-letter a DTO that couldn't be processed.

        Called by upsert services when individual DTOs fail permanently.
        """
        await self._dead_letter_dto(
            entity_type=entity_type,
            external_id=external_id,
            provider_slug=provider_slug,
            dto=dto,
            error=error,
            category=FailureCategory.PERMANENT,
            run_id=run_id,
        )

    # ── Internal ───────────────────────────────────────────────────────────

    async def _dead_letter_dto(
        self,
        entity_type: EntityType,
        external_id: str,
        provider_slug: str,
        dto: Any,
        error: Exception,
        category: FailureCategory,
        run_id: str = "",
    ) -> None:
        """Serialize and store a dead-letter record."""
        if self.dead_letter is None:
            return

        # Serialize DTO to dict
        try:
            dto_data = dto.__dict__ if hasattr(dto, "__dict__") else {"raw": str(dto)}
            # Remove non-serializable values
            dto_data = {
                k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                for k, v in dto_data.items()
                if not k.startswith("_")
            }
        except Exception:
            dto_data = {"error": "Could not serialize DTO"}

        record = DeadLetterRecord(
            entity_type=entity_type.value,
            external_id=external_id,
            provider_slug=provider_slug,
            dto_data=dto_data,
            error_message=str(error)[:500],
            error_type=type(error).__name__,
            failure_category=category.value,
            sync_run_id=run_id,
        )

        await self.dead_letter.add(record)

        # Fire event
        if self.events:
            event_ctx = SyncEventCtx(
                run_id=run_id,
                provider_slug=provider_slug,
            )
            await self.events.fire_failure(
                event_ctx, entity_type, error
            )


# ── Pre-built reliability presets ─────────────────────────────────────────────


def default_reliability(provider_slug: str) -> ReliabilityConfig:
    """Create a standard reliability config for a provider."""
    return ReliabilityConfig(
        circuit_breaker=CircuitBreaker(
            provider_slug=provider_slug,
            failure_threshold=5,
            recovery_timeout=60.0,
        ),
        dead_letter=DeadLetterQueue(),
        classifier=FailureClassifier(),
    )


def no_circuit_reliability(provider_slug: str) -> ReliabilityConfig:
    """Reliability without circuit breaking (for providers that are rock-solid)."""
    return ReliabilityConfig(
        circuit_breaker=None,
        dead_letter=DeadLetterQueue(),
        classifier=FailureClassifier(),
    )
