"""
Raw Data Lake — store every payload exactly as received, before any transformation.

Purpose: Never normalize immediately. Preserve source data for debugging,
          parser replay, schema change detection, and audit trails.

Storage: JSON files (production: S3/GCS/MinIO with Parquet).
Retention: 90 days raw, 1 year compressed archive.
"""

import gzip
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Raw Record
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RawRecord:
    """A single raw payload snapshot — immutable once stored."""
    id: str
    connector: str
    endpoint: str
    entity_type: str                                 # fighter, event, competition, etc.
    payload: dict[str, Any] | list[Any] | str
    content_type: str = "application/json"
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checksum: str = ""
    source_url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    status_code: int = 200
    job_id: str = ""
    request_id: str = ""
    version: int = 1

    def __post_init__(self):
        if not self.checksum and self.payload:
            raw = str(self.payload).encode()
            self.checksum = hashlib.sha256(raw).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Raw Data Store — per-entity typed stores
# ═══════════════════════════════════════════════════════════════════════════

class RawDataStore:
    """Base store for raw payloads. Subclassed per entity type."""

    def __init__(
        self,
        entity_type: str,
        base_dir: str = "/tmp/mma-raw",
        compression: bool = True,
        retention_days: int = 90,
    ):
        self.entity_type = entity_type
        self.base_dir = os.path.join(base_dir, entity_type)
        self.compression = compression
        self.retention_days = retention_days
        self._records: dict[str, RawRecord] = {}
        os.makedirs(self.base_dir, exist_ok=True)

    def store(self, record: RawRecord) -> str:
        """Store a raw payload. Returns the record ID."""
        self._records[record.id] = record
        self._write_to_disk(record)
        return record.id

    def get(self, record_id: str) -> Optional[RawRecord]:
        """Retrieve a stored raw record."""
        if record_id in self._records:
            return self._records[record_id]
        return self._read_from_disk(record_id)

    def list_by_connector(
        self, connector: str, limit: int = 100,
    ) -> list[RawRecord]:
        """List records from a specific connector."""
        matches = [
            r for r in self._records.values()
            if r.connector == connector
        ]
        return sorted(matches, key=lambda r: r.fetched_at, reverse=True)[:limit]

    def list_by_endpoint(
        self, endpoint: str, limit: int = 100,
    ) -> list[RawRecord]:
        """List records for a specific endpoint."""
        matches = [
            r for r in self._records.values()
            if r.endpoint == endpoint
        ]
        return sorted(matches, key=lambda r: r.fetched_at, reverse=True)[:limit]

    def find_duplicates(self, checksum: str) -> list[RawRecord]:
        """Find all records with the same checksum (potential duplicates)."""
        return [r for r in self._records.values() if r.checksum == checksum]

    def count(self) -> int:
        return len(self._records)

    def stats(self) -> dict:
        """Storage statistics."""
        connectors = {}
        for r in self._records.values():
            connectors.setdefault(r.connector, 0)
            connectors[r.connector] += 1
        return {
            "entity_type": self.entity_type,
            "total_records": len(self._records),
            "by_connector": connectors,
            "compression": self.compression,
            "retention_days": self.retention_days,
        }

    def archive(self, older_than_days: int = 90) -> int:
        """Archive records older than the threshold. Returns count archived."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        archived = 0
        to_remove = []
        for rid, record in self._records.items():
            try:
                fetched = datetime.fromisoformat(record.fetched_at)
                if fetched < cutoff:
                    self._write_archive(record)
                    to_remove.append(rid)
                    archived += 1
            except (ValueError, TypeError):
                pass
        for rid in to_remove:
            del self._records[rid]
        return archived

    def _write_to_disk(self, record: RawRecord):
        data = json.dumps({
            "id": record.id, "connector": record.connector,
            "endpoint": record.endpoint, "entity_type": record.entity_type,
            "payload": record.payload, "checksum": record.checksum,
            "fetched_at": record.fetched_at, "version": record.version,
        })
        if self.compression:
            data = gzip.compress(data.encode())
        path = os.path.join(self.base_dir, f"{record.id}.json.gz")
        with open(path, "wb") as f:
            f.write(data if self.compression else data.encode())

    def _read_from_disk(self, record_id: str) -> Optional[RawRecord]:
        path = os.path.join(self.base_dir, f"{record_id}.json.gz")
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            data = f.read()
        if self.compression:
            data = gzip.decompress(data)
        obj = json.loads(data)
        return RawRecord(
            id=obj["id"], connector=obj["connector"],
            endpoint=obj["endpoint"], entity_type=obj["entity_type"],
            payload=obj["payload"], checksum=obj.get("checksum", ""),
            fetched_at=obj.get("fetched_at", ""), version=obj.get("version", 1),
        )

    def _write_archive(self, record: RawRecord):
        archive_dir = os.path.join(self.base_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        path = os.path.join(archive_dir, f"{record.id}.json.gz")
        data = json.dumps({"id": record.id, "connector": record.connector,
                           "endpoint": record.endpoint, "payload": record.payload,
                           "checksum": record.checksum, "fetched_at": record.fetched_at})
        with open(path, "wb") as f:
            f.write(gzip.compress(data.encode()))


# Typed raw stores
class RawFighterStore(RawDataStore):
    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        super().__init__("fighters", base_dir)

class RawEventStore(RawDataStore):
    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        super().__init__("events", base_dir)

class RawFightStore(RawDataStore):
    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        super().__init__("fights", base_dir)

class RawRankingStore(RawDataStore):
    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        super().__init__("rankings", base_dir)

class RawPromotionStore(RawDataStore):
    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        super().__init__("promotions", base_dir)

class RawStatisticsStore(RawDataStore):
    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        super().__init__("statistics", base_dir)


# ═══════════════════════════════════════════════════════════════════════════
# Data Lake Manager — unified interface across all stores
# ═══════════════════════════════════════════════════════════════════════════

class DataLake:
    """Unified raw data lake — one interface for all entity types."""

    def __init__(self, base_dir: str = "/tmp/mma-raw"):
        self.fighters = RawFighterStore(base_dir)
        self.events = RawEventStore(base_dir)
        self.fights = RawFightStore(base_dir)
        self.rankings = RawRankingStore(base_dir)
        self.promotions = RawPromotionStore(base_dir)
        self.statistics = RawStatisticsStore(base_dir)
        self._all: dict[str, RawDataStore] = {
            "fighters": self.fighters, "events": self.events,
            "fights": self.fights, "rankings": self.rankings,
            "promotions": self.promotions, "statistics": self.statistics,
        }

    def store(self, record: RawRecord) -> str:
        store = self._all.get(record.entity_type)
        if store is None:
            raise ValueError(f"Unknown entity type: {record.entity_type}")
        return store.store(record)

    def get(self, entity_type: str, record_id: str) -> Optional[RawRecord]:
        store = self._all.get(entity_type)
        return store.get(record_id) if store else None

    def stats(self) -> dict:
        return {k: v.stats() for k, v in self._all.items()}

    def archive_all(self, older_than_days: int = 90) -> dict[str, int]:
        return {k: v.archive(older_than_days) for k, v in self._all.items()}

    def total_records(self) -> int:
        return sum(v.count() for v in self._all.values())
