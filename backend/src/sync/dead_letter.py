"""
Dead-letter queue — persistent storage for unrecoverable DTOs.

When a DTO cannot be processed (permanent error, data integrity violation),
it's stored here instead of being silently dropped. Operators can:
- Inspect dead letters to find data quality issues
- Retry individual DTOs after fixing the root cause
- Purge stale dead letters

File-based persistence: each dead letter is a JSON line in a file.
Production replacement: database-backed DeadLetterQueue.

Integrates with SyncEventBus: fires on_dead_letter events.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Dead Letter Record ────────────────────────────────────────────────────────


@dataclass
class DeadLetterRecord:
    """A single unrecoverable DTO stored for inspection."""

    entity_type: str
    external_id: str
    provider_slug: str
    dto_data: dict[str, Any]
    """The original DTO, serialized to dict."""

    error_message: str
    error_type: str
    failure_category: str

    recorded_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    retry_count: int = 0
    max_retries: int = 3

    # For correlation
    sync_run_id: str = ""
    job_name: str = ""

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries


# ── Dead Letter Queue ─────────────────────────────────────────────────────────


class DeadLetterQueue:
    """Persistent queue for unrecoverable DTOs.

    File-based: stores JSON lines in /.nexus/dead_letters/{provider}/
    Each line = one DeadLetterRecord.

    Usage:
        dlq = DeadLetterQueue("/.nexus/dead_letters")
        await dlq.add(record)
        records = dlq.list(provider_slug="espn", limit=50)
        await dlq.retry(record, retry_func)
        await dlq.purge(older_than_days=30)
    """

    def __init__(self, base_dir: str = "/.nexus/dead_letters") -> None:
        self._base_dir = Path(base_dir)

    # ── Write ──────────────────────────────────────────────────────────────

    async def add(self, record: DeadLetterRecord) -> None:
        """Persist a dead-letter record to disk."""
        dir_path = self._base_dir / record.provider_slug
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"{record.entity_type}.jsonl"

        try:
            with open(file_path, "a") as f:
                f.write(json.dumps(asdict(record), default=str) + "\n")
            logger.warning(
                f"Dead letter: {record.entity_type}/{record.external_id} "
                f"— {record.error_message[:100]}"
            )
        except Exception as e:
            logger.error(f"Failed to write dead letter: {e}")

    async def add_batch(self, records: list[DeadLetterRecord]) -> None:
        """Persist multiple dead-letter records."""
        for record in records:
            await self.add(record)

    # ── Read ────────────────────────────────────────────────────────────────

    def list(
        self,
        provider_slug: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
    ) -> list[DeadLetterRecord]:
        """List dead-letter records, newest first.

        Args:
            provider_slug: Filter by provider. None = all providers.
            entity_type: Filter by entity. None = all entities.
            limit: Max records to return.
        """
        records: list[DeadLetterRecord] = []

        if provider_slug:
            dirs = [self._base_dir / provider_slug]
        else:
            if not self._base_dir.exists():
                return []
            dirs = [
                d for d in self._base_dir.iterdir()
                if d.is_dir()
            ]

        for dir_path in dirs:
            if entity_type:
                files = [dir_path / f"{entity_type}.jsonl"]
            else:
                files = list(dir_path.glob("*.jsonl"))

            for file_path in files:
                if not file_path.exists():
                    continue
                try:
                    with open(file_path) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            data = json.loads(line)
                            records.append(DeadLetterRecord(**data))
                            if len(records) >= limit:
                                return records
                except Exception as e:
                    logger.error(f"Failed to read dead letters from {file_path}: {e}")

        # Sort newest first
        records.sort(key=lambda r: r.recorded_at, reverse=True)
        return records[:limit]

    def count(
        self,
        provider_slug: str | None = None,
        entity_type: str | None = None,
    ) -> int:
        """Count dead-letter records."""
        return len(self.list(provider_slug, entity_type, limit=100000))

    # ── Retry ───────────────────────────────────────────────────────────────

    def mark_retried(self, record: DeadLetterRecord) -> None:
        """Mark a record as retried (increment counter)."""
        record.retry_count += 1
        if record.retry_count >= record.max_retries:
            logger.info(
                f"Dead letter exhausted: {record.entity_type}/{record.external_id} "
                f"(retries={record.retry_count})"
            )

    # ── Purge ───────────────────────────────────────────────────────────────

    async def purge(
        self,
        provider_slug: str | None = None,
        older_than_days: int | None = None,
    ) -> int:
        """Delete dead-letter records. Returns number purged.

        Args:
            provider_slug: Filter by provider. None = all.
            older_than_days: Only purge records older than N days.
                            None = purge all matching records.
        """
        purged = 0
        now = datetime.now(UTC)

        if provider_slug:
            dirs = [self._base_dir / provider_slug]
        else:
            if not self._base_dir.exists():
                return 0
            dirs = [d for d in self._base_dir.iterdir() if d.is_dir()]

        for dir_path in dirs:
            for file_path in dir_path.glob("*.jsonl"):
                if not file_path.exists():
                    continue
                try:
                    lines: list[str] = []
                    with open(file_path) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            data = json.loads(line)
                            recorded_at = datetime.fromisoformat(
                                data.get("recorded_at", "2000-01-01T00:00:00")
                            )
                            if older_than_days is not None:
                                age = (now - recorded_at).days
                                if age < older_than_days:
                                    lines.append(json.dumps(data) + "\n")
                                    continue
                            purged += 1
                    # Rewrite file without purged records
                    with open(file_path, "w") as f:
                        f.writelines(lines)
                except Exception as e:
                    logger.error(f"Failed to purge {file_path}: {e}")

        logger.info(f"Purged {purged} dead-letter records")
        return purged

    def stats(self, provider_slug: str | None = None) -> dict[str, int]:
        """Return per-entity counts for a provider."""
        counts: dict[str, int] = {}
        for record in self.list(provider_slug=provider_slug, limit=100000):
            key = record.entity_type
            counts[key] = counts.get(key, 0) + 1
        return counts
