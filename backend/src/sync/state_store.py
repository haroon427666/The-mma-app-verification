"""
SyncStateStore — interface for persisting and loading SyncState.

The engine loads state before each job and saves it after.
Implementations: DatabaseSyncStateStore (PostgreSQL, production),
MemorySyncStateStore (in-memory dict, tests).
"""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from src.sync.state import SyncState
from src.sync.types import EntityType


@runtime_checkable
class SyncStateStore(Protocol):
    """Protocol for persisting per-entity sync state.

    Implementations:
    - DatabaseSyncStateStore: persists to PostgreSQL (production)
    - MemorySyncStateStore: in-memory dict (tests)
    - RedisSyncStateStore: Redis-backed (future, multi-worker)
    """

    async def load(
        self, entity_type: EntityType, provider_slug: str
    ) -> SyncState | None:
        """Load saved state. Returns None if no state exists (first run)."""
        ...

    async def save(self, state: SyncState) -> None:
        """Persist state to storage after a job completes."""
        ...


class MemorySyncStateStore:
    """In-memory state store for testing.

    Not a Protocol implementation — this is the concrete test double.
    """

    def __init__(self) -> None:
        self._store: dict[str, SyncState] = {}

    def _key(self, entity_type: EntityType, provider_slug: str) -> str:
        return f"{provider_slug}:{entity_type.value}"

    async def load(
        self, entity_type: EntityType, provider_slug: str
    ) -> SyncState | None:
        return self._store.get(self._key(entity_type, provider_slug))

    async def save(self, state: SyncState) -> None:
        self._store[self._key(state.entity_type, state.provider_slug)] = state


class DatabaseSyncStateStore:
    """DB-backed SyncState persistence via the existing checkpoint table.

    Serializes SyncState into the existing `sync_checkpoints` row (scalar
    columns stay meaningful: last_offset/last_page/status/completed) plus the
    `data` JSON payload for the fields without a dedicated column. Uses the
    existing CheckpointManager — no parallel checkpoint system.

    Commits after every save so a hard kill never loses job progress.
    """

    def __init__(self, session: Any) -> None:
        from src.sync.checkpoints import CheckpointManager

        self._session = session
        self._manager = CheckpointManager(session)

    async def load(
        self, entity_type: EntityType, provider_slug: str
    ) -> SyncState | None:
        checkpoint = await self._manager.load(entity_type.value, provider_slug)
        if checkpoint is None:
            return None
        state = _state_from_data(checkpoint.data or {})
        # Scalar columns are authoritative (they are kept in sync at save time);
        # the data payload fills in the rest.
        state.entity_type = entity_type
        state.provider_slug = provider_slug
        state.last_offset = checkpoint.last_offset
        state.last_page = checkpoint.last_page
        state.total_records = checkpoint.total_records
        state.status = checkpoint.status
        state.error_msg = checkpoint.last_error
        return state

    async def save(self, state: SyncState) -> None:
        from src.sync.checkpoints import Checkpoint

        checkpoint = Checkpoint(
            entity_type=state.entity_type.value,
            provider=state.provider_slug,
            last_offset=state.last_offset,
            last_page=state.last_page,
            total_records=state.total_records,
            status=state.status,
            last_error=state.error_msg,
            completed=state.status == "COMPLETED",
        )
        await self._manager.save(checkpoint, data=_state_to_data(state))
        await self._session.commit()


# ── SyncState ↔ JSON serialization ──────────────────────────────────────────


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _state_to_data(state: SyncState) -> dict[str, Any]:
    return {
        "entity_type": state.entity_type.value,
        "provider_slug": state.provider_slug,
        "last_successful_sync": _iso(state.last_successful_sync),
        "last_attempt": _iso(state.last_attempt),
        "last_failure": _iso(state.last_failure),
        "last_cursor": state.last_cursor,
        "total_pages": state.total_pages,
        "etag": state.etag,
        "updated_since": _iso(state.updated_since),
        "last_modified": _iso(state.last_modified),
        "checkpoint": state.checkpoint,
        "consecutive_failures": state.consecutive_failures,
        "provider_schema_version": state.provider_schema_version,
        "total_synced": state.total_synced,
        "total_records": state.total_records,
        "total_errors": state.total_errors,
    }


def _state_from_data(data: dict[str, Any]) -> SyncState:
    """Rebuild a SyncState from a serialized payload. Unknown/missing keys
    fall back to fresh defaults (forward compatible)."""
    try:
        entity_type = EntityType(data.get("entity_type", "fighter"))
    except ValueError:
        entity_type = EntityType.FIGHTER
    return SyncState(
        entity_type=entity_type,
        provider_slug=data.get("provider_slug", "espn"),
        last_successful_sync=_parse_iso(data.get("last_successful_sync")),
        last_attempt=_parse_iso(data.get("last_attempt")),
        last_failure=_parse_iso(data.get("last_failure")),
        last_cursor=data.get("last_cursor"),
        last_offset=int(data.get("last_offset") or 0),
        last_page=int(data.get("last_page") or 0),
        total_pages=int(data.get("total_pages") or 0),
        etag=data.get("etag"),
        updated_since=_parse_iso(data.get("updated_since")),
        last_modified=_parse_iso(data.get("last_modified")),
        checkpoint=data.get("checkpoint") or {},
        status=data.get("status", "PENDING"),
        error_msg=data.get("error_msg"),
        consecutive_failures=int(data.get("consecutive_failures") or 0),
        provider_schema_version=int(data.get("provider_schema_version") or 1),
        total_synced=int(data.get("total_synced") or 0),
        total_records=int(data.get("total_records") or 0),
        total_errors=int(data.get("total_errors") or 0),
    )
