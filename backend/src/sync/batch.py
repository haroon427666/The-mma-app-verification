"""
SyncBatch — a batch of DTOs with metadata flowing through the pipeline.

Rather than passing raw list[DTO] around, SyncBatch carries:
- The DTOs themselves
- Page/cursor info for checkpointing
- Timing for per-batch metrics
- Whether this is the final batch
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncBatch:
    """A batch of DTOs with pagination context.

    Passed from provider fetch → transform → upsert in the pipeline.
    """

    # ── Data ───────────────────────────────────────────────────────────────
    items: list[Any] = field(default_factory=list)
    """The DTOs in this batch."""

    # ── Pagination context ─────────────────────────────────────────────────
    page: int = 0
    """Current page number (1-based)."""

    total_pages: int = 0
    """Total pages known from the provider (0 if unknown)."""

    cursor: str | None = None
    """Provider cursor/continuation token for the next page."""

    is_last: bool = False
    """True if this is the final batch."""

    # ── Stats ──────────────────────────────────────────────────────────────
    items_before_transform: int = 0
    """Item count before _transform() was applied."""

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0
