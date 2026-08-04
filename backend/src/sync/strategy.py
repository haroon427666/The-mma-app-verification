"""
Sync strategy — determines sync mode and fetch parameters.

Decides full vs incremental vs resume based on:
- SyncState (checkpoint, last_sync, cursor, page)
- ProviderCapabilities (supports_incremental, pagination type)
- Requested SyncMode (FULL, INCREMENTAL, RESUME, FORCE)

Returns a SyncDecision with the resolved mode and fetch parameters.
The pipeline uses this to drive pagination and data retrieval.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

from src.sync.state import SyncState
from src.sync.types import (
    EntityType,
    ProviderCapabilities,
    SyncMode,
)

logger = logging.getLogger(__name__)


# ── Sync Decision ─────────────────────────────────────────────────────────────


@dataclass
class SyncDecision:
    """Resolved sync mode and fetch parameters for one job execution.

    The pipeline uses this to:
    - Decide whether to pass updated_since to the provider
    - Set the starting page/offset for pagination
    - Skip already-synced data on resume
    """

    mode: SyncMode
    """FULL, INCREMENTAL, RESUME, or FORCE."""

    entity_type: EntityType

    # Pagination
    start_page: int = 0
    start_offset: int = 0
    cursor: str | None = None
    """Cursor from last sync — passed to provider for continuation."""

    # Incremental
    updated_since: datetime | None = None
    """Only fetch entities changed after this timestamp."""

    # Rationale for logging
    reason: str = ""

    @property
    def is_full(self) -> bool:
        return self.mode in (SyncMode.FULL, SyncMode.FORCE)

    @property
    def is_resume(self) -> bool:
        return self.mode == SyncMode.RESUME

    @property
    def is_incremental(self) -> bool:
        return self.mode == SyncMode.INCREMENTAL

    @property
    def is_resuming_from_checkpoint(self) -> bool:
        """True if we should skip already-synced data."""
        return self.start_page > 0 or self.start_offset > 0 or self.cursor is not None

    def __eq__(self, other: object) -> bool:
        """Decisions are equal when their resolved mode matches."""
        if isinstance(other, SyncDecision):
            return self.mode == other.mode
        return NotImplemented

    # Enum-like constants for ergonomic comparisons:
    #     decision = strategy.decide(...)
    #     assert decision == SyncDecision.FULL
    FULL: ClassVar["SyncDecision"]
    INCREMENTAL: ClassVar["SyncDecision"]
    RESUME: ClassVar["SyncDecision"]
    FORCE: ClassVar["SyncDecision"]


SyncDecision.FULL = SyncDecision(mode=SyncMode.FULL, entity_type=EntityType.FIGHTER)
SyncDecision.INCREMENTAL = SyncDecision(
    mode=SyncMode.INCREMENTAL, entity_type=EntityType.FIGHTER
)
SyncDecision.RESUME = SyncDecision(mode=SyncMode.RESUME, entity_type=EntityType.FIGHTER)
SyncDecision.FORCE = SyncDecision(mode=SyncMode.FORCE, entity_type=EntityType.FIGHTER)


# ── Sync Strategy ─────────────────────────────────────────────────────────────


class SyncStrategy:
    """Decides sync mode based on state, capabilities, and request.

    Usage:
        strategy = SyncStrategy()
        decision = strategy.decide(
            state=sync_state,
            capabilities=provider_capabilities,
            requested=SyncMode.INCREMENTAL,
        )
        # decision.mode → INCREMENTAL | FULL | RESUME | FORCE
    """

    # How long after a successful sync before incremental is preferred again
    INCREMENTAL_THRESHOLD_HOURS: int = 4

    def decide(
        self,
        state: SyncState,
        capabilities: ProviderCapabilities | None = None,
        requested: SyncMode | None = None,
        force: bool = False,
    ) -> SyncDecision:
        """Determine sync mode and fetch parameters.

        Decision tree:
        ┌─ FORCE requested (or force=True)? → FULL from page 0, clear checkpoint
        ├─ RESUME requested? → RESUME from last page + cursor
        ├─ INCREMENTAL requested?
        │   ├─ Provider supports it + has recent sync? → INCREMENTAL
        │   └─ Otherwise → FULL
        ├─ Crashed mid-run (state.status=FAILED/IN_PROGRESS)?
        │   └─ RESUME from last checkpoint
        ├─ First ever run? → FULL from page 0
        ├─ Recent successful sync?
        │   ├─ Provider supports incremental? → INCREMENTAL
        │   └─ Otherwise → FULL
        └─ Stale sync (>threshold)? → FULL
        """
        entity = state.entity_type

        # FORCE: always full, clear checkpoint
        if force or requested == SyncMode.FORCE:
            return SyncDecision(
                mode=SyncMode.FULL,
                entity_type=entity,
                reason="FORCE requested — full resync",
            )

        # RESUME: continue from last checkpoint
        if requested == SyncMode.RESUME:
            return self._decide_resume(state, entity)

        # INCREMENTAL requested
        if requested == SyncMode.INCREMENTAL:
            return self._decide_incremental(state, capabilities, entity)

        # Auto-detect from state
        return self._decide_auto(state, capabilities, entity)

    # ── Mode-specific decisions ────────────────────────────────────────────

    def _decide_resume(
        self, state: SyncState, entity: EntityType
    ) -> SyncDecision:
        """Resume from last checkpoint."""
        entity_label = getattr(entity, "value", entity)
        if state.last_page == 0 and not state.last_cursor and state.last_offset == 0:
            logger.info(f"{entity_label}: RESUME requested but no checkpoint — full sync")
            return SyncDecision(
                mode=SyncMode.FULL,
                entity_type=entity,
                reason="No checkpoint to resume from",
            )

        logger.info(
            f"{entity_label}: RESUME from page={state.last_page} "
            f"offset={state.last_offset} cursor={state.last_cursor}"
        )
        return SyncDecision(
            mode=SyncMode.RESUME,
            entity_type=entity,
            start_page=state.last_page,
            start_offset=state.last_offset,
            cursor=state.last_cursor,
            reason=f"Resuming from checkpoint (page {state.last_page})",
        )

    def _decide_incremental(
        self,
        state: SyncState,
        capabilities: ProviderCapabilities | None,
        entity: EntityType,
    ) -> SyncDecision:
        """Attempt incremental — fall back to full if not supported."""
        entity_label = getattr(entity, "value", entity)
        if not capabilities or not capabilities.supports_incremental:
            logger.info(
                f"{entity_label}: INCREMENTAL requested but provider "
                f"doesn't support it — full sync"
            )
            return SyncDecision(
                mode=SyncMode.FULL,
                entity_type=entity,
                reason="Provider does not support incremental sync",
            )

        if state.last_successful_sync is None:
            logger.info(
                f"{entity_label}: INCREMENTAL requested but no prior sync — full sync"
            )
            return SyncDecision(
                mode=SyncMode.FULL,
                entity_type=entity,
                reason="No prior successful sync for delta reference",
            )

        # Use last successful sync as the cutoff
        return SyncDecision(
            mode=SyncMode.INCREMENTAL,
            entity_type=entity,
            updated_since=state.last_successful_sync,
            reason=(
                f"Incremental from "
                f"{state.last_successful_sync.isoformat()}"
            ),
        )

    def _decide_auto(
        self,
        state: SyncState,
        capabilities: ProviderCapabilities | None,
        entity: EntityType,
    ) -> SyncDecision:
        """Auto-detect mode from current state."""
        entity_label = getattr(entity, "value", entity)

        # Crashed or in-progress → resume
        if state.status in ("FAILED", "IN_PROGRESS"):
            if state.last_page > 0 or state.last_cursor or state.last_offset > 0:
                return self._decide_resume(state, entity)
            logger.info(f"{entity_label}: Crashed with no checkpoint — full sync")
            return SyncDecision(
                mode=SyncMode.FULL,
                entity_type=entity,
                reason=f"Previous run {state.status} with no checkpoint",
            )

        # First run → full
        if state.last_successful_sync is None:
            return SyncDecision(
                mode=SyncMode.FULL,
                entity_type=entity,
                reason="First sync run",
            )

        last_successful_sync = state.last_successful_sync

        # Recent sync → incremental if supported (or capabilities unknown)
        if capabilities is None or capabilities.supports_incremental:
            hours_since = (
                datetime.now(UTC) - last_successful_sync
            ).total_seconds() / 3600
            if hours_since < self.INCREMENTAL_THRESHOLD_HOURS:
                return SyncDecision(
                    mode=SyncMode.INCREMENTAL,
                    entity_type=entity,
                    updated_since=last_successful_sync,
                    reason=f"Recent sync ({hours_since:.0f}h ago) — incremental",
                )

        # Stale → full
        return SyncDecision(
            mode=SyncMode.FULL,
            entity_type=entity,
            reason="Stale sync — full refresh",
        )
