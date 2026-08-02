"""Prometheus Metrics — observability for the sync service.

Exposes standard sync metrics for monitoring dashboards.
No external dependencies needed — uses a lightweight registry.

Metrics exposed:
    sync_job_duration_seconds{job}     — Histogram of job durations
    sync_job_total{job, status}        — Counter of job runs
    sync_records_total{job, operation} — Insert/update/skip/error counts
    sync_provider_errors_total{provider} — Provider error counter
    sync_queue_size                     — Current queue depth
    sync_live_mode                      — 1 if live mode active
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Counter:
    name: str
    value: int = 0
    labels: dict[str, str] = field(default_factory=dict)

    def inc(self, amount: int = 1) -> None:
        self.value += amount


@dataclass
class Gauge:
    name: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)

    def set(self, value: float) -> None:
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        self.value -= amount


class MetricsRegistry:
    """Lightweight Prometheus-compatible metrics registry.

    Exports metrics in Prometheus text format via the /metrics endpoint.
    No external dependency — works without prometheus_client.
    """

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._started_at = datetime.now(timezone.utc)

    # ── Registration ────────────────────────────────────────────────────

    def counter(self, name: str, **labels) -> Counter:
        key = self._make_key(name, labels)
        if key not in self._counters:
            self._counters[key] = Counter(name=name, labels=labels)
        return self._counters[key]

    def gauge(self, name: str, **labels) -> Gauge:
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = Gauge(name=name, labels=labels)
        return self._gauges[key]

    def _make_key(self, name: str, labels: dict) -> str:
        parts = [name] + [f"{k}={v}" for k, v in sorted(labels.items())]
        return "|".join(parts)

    # ── Record ──────────────────────────────────────────────────────────

    def record_job_duration(self, job_name: str, duration_ms: float) -> None:
        c = self.counter("sync_job_duration_seconds_total", job=job_name)
        c.inc()  # Count of runs
        g = self.gauge("sync_job_duration_seconds", job=job_name)
        g.set(duration_ms / 1000.0)

    def record_job_result(
        self, job_name: str, status: str, inserted: int = 0, updated: int = 0, errors: int = 0,
    ) -> None:
        self.counter("sync_job_total", job=job_name, status=status).inc()
        self.counter("sync_records_total", job=job_name, operation="inserted").inc(inserted)
        self.counter("sync_records_total", job=job_name, operation="updated").inc(updated)
        self.counter("sync_records_total", job=job_name, operation="errors").inc(errors)

    def record_provider_error(self, provider: str) -> None:
        self.counter("sync_provider_errors_total", provider=provider).inc()

    def set_queue_size(self, size: int) -> None:
        self.gauge("sync_queue_size").set(size)

    def set_live_mode(self, active: bool) -> None:
        self.gauge("sync_live_mode").set(1 if active else 0)

    # ── Export ──────────────────────────────────────────────────────────

    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus text format."""
        lines = [
            "# HELP sync_up Time since the sync service started.",
            "# TYPE sync_up gauge",
            f"sync_up {int((datetime.now(timezone.utc) - self._started_at).total_seconds())}",
        ]

        for _, counter in self._counters.items():
            label_str = self._format_labels(counter.labels)
            lines.extend([
                f"# HELP {counter.name} Auto-generated counter metric.",
                f"# TYPE {counter.name} counter",
                f"{counter.name}{label_str} {counter.value}",
            ])

        for _, gauge in self._gauges.items():
            label_str = self._format_labels(gauge.labels)
            lines.extend([
                f"# HELP {gauge.name} Auto-generated gauge metric.",
                f"# TYPE {gauge.name} gauge",
                f"{gauge.name}{label_str} {gauge.value}",
            ])

        return "\n".join(lines) + "\n"

    def _format_labels(self, labels: dict) -> str:
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(parts) + "}"


# Singleton
metrics = MetricsRegistry()
