"""
Sync metrics — strongly-typed counters and timings for a single sync run.

No dict lookups, no string keys for metrics. Every metric is a named field
on a typed class. Prometheus/Grafana integration maps directly to these fields.
"""

import time
from dataclasses import dataclass, field


# ── Sub-metrics (strongly typed, no dicts) ────────────────────────────────────


@dataclass
class ProviderMetrics:
    """Metrics for provider API calls."""

    calls: int = 0              # Total HTTP requests
    latency_ms: float = 0.0     # Total time waiting for provider
    errors: int = 0             # Failed requests
    rate_limited: int = 0       # 429 responses received
    bytes_downloaded: int = 0   # Approximate response size

    @property
    def avg_latency_ms(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.latency_ms / self.calls


@dataclass
class DatabaseMetrics:
    """Metrics for database writes."""

    inserts: int = 0            # Rows inserted
    updates: int = 0            # Rows updated
    deletes: int = 0            # Rows deleted
    skips: int = 0              # Rows skipped (unchanged)
    errors: int = 0             # Write failures
    latency_ms: float = 0.0     # Total time in DB writes
    transactions: int = 0       # Number of commits


@dataclass
class HttpMetrics:
    """Metrics for HTTP-level concerns."""

    total_requests: int = 0
    total_2xx: int = 0
    total_4xx: int = 0
    total_5xx: int = 0
    total_timeouts: int = 0
    total_retries: int = 0


# ── Per-Entity Metrics ────────────────────────────────────────────────────────


@dataclass
class EntityMetrics:
    """Metrics for one entity type during a sync run.

    Keys are typed fields, never dict lookups.
    """

    entity_type: str = ""
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: float = 0.0


# ── Aggregate Sync Metrics ────────────────────────────────────────────────────


@dataclass
class SyncMetrics:
    """Thread-safe metrics accumulator for a single sync run.

    Contains three sub-metrics groups (provider, database, HTTP)
    plus per-entity breakdowns.

    Usage:
        metrics = SyncMetrics()
        metrics.provider.calls += 1
        metrics.entity("fighters").inserted += 100
        metrics.start_db_timer()
        # ... upsert ...
        metrics.stop_db_timer()
    """

    # Sub-metrics
    provider: ProviderMetrics = field(default_factory=ProviderMetrics)
    database: DatabaseMetrics = field(default_factory=DatabaseMetrics)
    http: HttpMetrics = field(default_factory=HttpMetrics)

    # Per-entity breakdown
    entities: dict[str, EntityMetrics] = field(default_factory=dict)

    # Internal timing
    _start_time: float = field(default_factory=time.monotonic, repr=False)
    _timer_start: float = 0.0

    # ── Entity access ───────────────────────────────────────────────────────

    def entity(self, entity_type: str) -> EntityMetrics:
        """Get or create metrics for an entity type."""
        if entity_type not in self.entities:
            self.entities[entity_type] = EntityMetrics(entity_type=entity_type)
        return self.entities[entity_type]

    # ── Timing helpers ─────────────────────────────────────────────────────

    def start_provider_timer(self) -> None:
        self._timer_start = time.monotonic()

    def stop_provider_timer(self) -> None:
        self.provider.latency_ms += (time.monotonic() - self._timer_start) * 1000

    def start_db_timer(self) -> None:
        self._timer_start = time.monotonic()

    def stop_db_timer(self) -> None:
        self.database.latency_ms += (time.monotonic() - self._timer_start) * 1000

    # ── Aggregate properties ───────────────────────────────────────────────

    @property
    def total_duration_ms(self) -> float:
        return (time.monotonic() - self._start_time) * 1000

    @property
    def total_inserted(self) -> int:
        return sum(e.inserted for e in self.entities.values())

    @property
    def total_updated(self) -> int:
        return sum(e.updated for e in self.entities.values())

    @property
    def total_skipped(self) -> int:
        return sum(e.skipped for e in self.entities.values())

    @property
    def total_errors(self) -> int:
        return sum(e.errors for e in self.entities.values())

    # ── Prometheus-ready summary ───────────────────────────────────────────

    def summary(self) -> dict:
        """JSON-serializable summary for structured logging and monitoring."""
        return {
            "duration_ms": round(self.total_duration_ms, 1),
            "provider": {
                "calls": self.provider.calls,
                "latency_ms": round(self.provider.latency_ms, 1),
                "avg_latency_ms": round(self.provider.avg_latency_ms, 1),
                "errors": self.provider.errors,
                "rate_limited": self.provider.rate_limited,
            },
            "database": {
                "inserts": self.database.inserts,
                "updates": self.database.updates,
                "skips": self.database.skips,
                "errors": self.database.errors,
                "latency_ms": round(self.database.latency_ms, 1),
                "transactions": self.database.transactions,
            },
            "http": {
                "total": self.http.total_requests,
                "2xx": self.http.total_2xx,
                "4xx": self.http.total_4xx,
                "5xx": self.http.total_5xx,
                "timeouts": self.http.total_timeouts,
                "retries": self.http.total_retries,
            },
            "entities": {
                entity_type: {
                    "inserted": m.inserted,
                    "updated": m.updated,
                    "skipped": m.skipped,
                    "errors": m.errors,
                    "duration_ms": round(m.duration_ms, 1),
                }
                for entity_type, m in self.entities.items()
            },
        }
