"""
SyncStateStore — interface for persisting and loading SyncState.

The engine loads state before each job and saves it after.
Implementations: DatabaseSyncStateStore (PostgreSQL, production),
MemorySyncStateStore (in-memory dict, tests).
"""

from typing import Protocol, runtime_checkable

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
