"""
Production Hardening — health checks, benchmarks, operational docs, runbooks.

Phase 19.12 — Final platform audit and production readiness verification.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable

# ═══════════════════════════════════════════════════════════════════════════
# Health Check System
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class HealthCheck:
    name: str
    status: str                    # healthy, degraded, down
    latency_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """Aggregate health checks across all platform components."""

    def __init__(self):
        self._checks: list[tuple[str, Callable[[], HealthCheck]]] = []

    def register(self, name: str, check_fn: Callable[[], HealthCheck]):
        self._checks.append((name, check_fn))

    def run_all(self) -> dict:
        results = []
        for name, check_fn in self._checks:
            start = time.monotonic()
            try:
                result = check_fn()
                results.append(result)
            except Exception as e:
                results.append(HealthCheck(
                    name=name, status="down",
                    latency_ms=(time.monotonic() - start) * 1000,
                    message=str(e),
                ))

        healthy = sum(1 for r in results if r.status == "healthy")
        degraded = sum(1 for r in results if r.status == "degraded")
        down = sum(1 for r in results if r.status == "down")

        overall = "healthy"
        if down > 0:
            overall = "degraded" if healthy > 0 else "down"
        elif degraded > 0:
            overall = "degraded"

        return {
            "status": overall,
            "checks": [
                {"name": r.name, "status": r.status, "latency_ms": round(r.latency_ms, 1),
                 "message": r.message}
                for r in results
            ],
            "summary": {"healthy": healthy, "degraded": degraded, "down": down},
            "total": len(results),
        }

    def run_liveness(self) -> dict:
        return {"status": "alive", "timestamp": time.time()}

    def run_readiness(self) -> dict:
        result = self.run_all()
        return {"ready": result["status"] == "healthy", "checks": result["checks"]}


# ═══════════════════════════════════════════════════════════════════════════
# Benchmarks
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Benchmark:
    name: str
    iterations: int
    total_ms: float
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float


def run_benchmark(
    name: str, fn: Callable, iterations: int = 100, warmup: int = 10,
) -> Benchmark:
    """Run a performance benchmark and return statistics."""
    # Warmup
    for _ in range(warmup):
        fn()

    # Measure
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)

    times.sort()
    total = sum(times)
    n = len(times)
    return Benchmark(
        name=name, iterations=iterations,
        total_ms=total, avg_ms=total / n,
        p50_ms=times[int(n * 0.50)],
        p95_ms=times[int(n * 0.95)],
        p99_ms=times[int(n * 0.99)],
        min_ms=times[0], max_ms=times[-1],
    )


def run_all_benchmarks() -> list[Benchmark]:
    """Run standard benchmarks across all platform components."""
    benchmarks = []

    # Normalization benchmark
    def bench_normalize():
        from platform.normalization import lbs_to_kg, inches_to_cm, name_similarity
        lbs_to_kg(155), inches_to_cm(66)
        name_similarity("Islam Makhachev", "Islam Makachev")

    benchmarks.append(run_benchmark("normalization_ops", bench_normalize, 500))

    # Identity benchmark
    def bench_identity():
        from platform.identity import levenshtein, SimilarityEngine
        levenshtein("Islam Makhachev", "Islam Makachev")
        SimilarityEngine.compare_fighters(
            {"full_name": "Islam", "last_name": "M", "birth_date": "1991-10-27",
             "nationality": "Russia", "height_cm": 178},
            {"full_name": "Islam", "last_name": "M", "birth_date": "1991-10-27",
             "nationality": "Russia", "height_cm": 178},
        )

    benchmarks.append(run_benchmark("identity_ops", bench_identity, 100))

    # Quality benchmark
    def bench_quality():
        from platform.quality import QualityEngine
        engine = QualityEngine()
        engine.assess_fighter({
            "first_name": "Islam", "last_name": "Makhachev",
            "wins": 21, "losses": 1, "height_cm": 178, "weight_kg": 70.3,
        })

    benchmarks.append(run_benchmark("quality_ops", bench_quality, 50))

    return benchmarks


# ═══════════════════════════════════════════════════════════════════════════
# Operational Runbooks
# ═══════════════════════════════════════════════════════════════════════════

RUNBOOKS = {
    "provider_down": {
        "title": "Data provider is unavailable",
        "symptoms": ["Connector status: DOWN", "Circuit breaker: OPEN",
                      "Health check failing for >3 consecutive polls"],
        "severity": "P2 — degraded",
        "response": [
            "1. Check provider health endpoint manually",
            "2. Verify network connectivity from platform",
            "3. Check rate limit status — wait if rate-limited",
            "4. If rate-limited: reduce ingestion frequency temporarily",
            "5. If provider is genuinely down: circuit breaker auto-opens after 5 failures",
            "6. Auto-recovery: HALF_OPEN state on reset timeout, CLOSED on success",
        ],
        "recovery_time": "Self-healing within 60s (circuit breaker reset)",
    },
    "sync_stuck": {
        "title": "Synchronization job stuck or hung",
        "symptoms": ["Job running >2x timeout_seconds", "No progress in 10 minutes"],
        "severity": "P3 — minor",
        "response": [
            "1. Cancel the hung job via scheduler dashboard",
            "2. Check dead-letter queue for any batch failures",
            "3. Re-trigger job manually with --entity flag",
            "4. If persistent: increase timeout_seconds in JobDefinition",
        ],
        "recovery_time": "Minutes (manual cancellation + retry)",
    },
    "data_quality_drop": {
        "title": "Data quality score dropped significantly",
        "symptoms": ["Quality tier degraded (excellent→good or good→fair)",
                      "Warning count increased >50%"],
        "severity": "P3 — minor",
        "response": [
            "1. Check which dimension degraded (completeness/freshness/accuracy)",
            "2. If freshness: trigger manual sync for affected entity type",
            "3. If completeness: check if provider schema changed",
            "4. If accuracy: check for source conflicts — resolve manually",
            "5. If quality stays low >24h: flag affected entities for manual review",
        ],
        "recovery_time": "Hours (depends on cause)",
    },
    "identity_conflict": {
        "title": "Identity resolution conflict detected",
        "symptoms": ["Multiple sources disagree on fighter identity",
                      "Manual review queue growing"],
        "severity": "P4 — informational",
        "response": [
            "1. Review flagged matches in resolution dashboard",
            "2. Verify with authoritative source (UFC/ESPN)",
            "3. Accept or reject merge suggestion",
            "4. If rejected: register alias if name is slightly different",
            "5. Monitor for similar conflicts in same weight class/promotion",
        ],
        "recovery_time": "Per-entity (manual review)",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# Production Readiness Checklist
# ═══════════════════════════════════════════════════════════════════════════

PRODUCTION_CHECKLIST = {
    "scheduler": [
        "All 20+ jobs registered in scheduler_jobs",
        "Dependency graph validated — no cycles",
        "Distributed locks prevent duplicate execution",
        "Dead-letter queue replay operational",
        "Graceful shutdown preserves job state",
        "Worker pool handles concurrent jobs",
    ],
    "connectors": [
        "All 7 connector presets configured",
        "Rate limiting active per connector",
        "Circuit breaker protects against provider outages",
        "Health checks running every 60s",
        "Auth tokens rotated automatically",
    ],
    "data_lake": [
        "Raw payloads stored with SHA-256 checksums",
        "90-day retention with compression",
        "Archive pipeline operational",
        "Replay capability verified",
    ],
    "normalization": [
        "Canonical models defined for all 6 entity types",
        "Unit converters validated (lbs→kg, in→cm)",
        "Schema validator catches out-of-range values",
    ],
    "identity": [
        "Cross-source matching operational (>0.85 auto-merge)",
        "Merge audit trail complete",
        "Unmerge/reversibility tested",
        "Alias database populated",
    ],
    "quality": [
        "5-dimension quality scoring active",
        "Quality tiers assigned per entity",
        "Auto-rescoring after updates",
        "Quality degradation alerts configured",
    ],
    "trust": [
        "Source trust scores computed from 6 metrics",
        "Auto-tiering (primary/secondary/enrichment)",
        "Source health monitoring active",
    ],
    "lineage": [
        "Audit trail records every field change",
        "Entity snapshots preserved (10 versions)",
        "Diff engine operational",
        "Rollback to any version supported",
    ],
}
