"""
Source Reliability & Trust System — automatic trust scoring for every data source.

Every source receives a dynamic trust score based on:
- Historical accuracy (compared to consensus)
- Uptime (connector health)
- Freshness (how recently data was updated)
- Completeness (field coverage %)
- Conflict frequency (how often this source disagrees)
- Latency (response time trends)

Trust scores decay over time and auto-recover on good behavior.
Sources with very low trust are automatically deprioritized.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime as _dt, timezone as _tz
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Source Profile
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SourceProfile:
    """Trust profile for a single data source."""
    name: str
    trust_score: float = 0.5             # 0.0 — 1.0, starts neutral
    accuracy_history: list[float] = field(default_factory=list)
    uptime_history: list[float] = field(default_factory=list)
    freshness_avg_days: float = 0.0
    completeness_pct: float = 0.0
    conflict_count: int = 0
    conflict_total: int = 0
    latency_avg_ms: float = 0.0
    last_validated: str = ""
    status: str = "unknown"              # healthy, degraded, down, disabled
    tier: str = "secondary"             # primary, secondary, enrichment, unverified
    recommendation: str = ""

    def __post_init__(self):
        if not self.last_validated:
            self.last_validated = _dt.now(_tz.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# Trust Engine
# ═══════════════════════════════════════════════════════════════════════════

class TrustEngine:
    """Computes and maintains trust scores for all data sources."""

    # Scoring weights
    WEIGHTS = {
        "accuracy": 0.35,
        "uptime": 0.15,
        "freshness": 0.15,
        "completeness": 0.15,
        "conflict_rate": 0.15,
        "latency": 0.05,
    }

    # Tier assignments
    TIER_THRESHOLDS = {
        "primary": 0.75,
        "secondary": 0.55,
        "enrichment": 0.35,
    }

    def __init__(self):
        self._sources: dict[str, SourceProfile] = {}

    def register_source(
        self, name: str, initial_trust: float = 0.5,
        tier: str = "secondary",
    ) -> SourceProfile:
        profile = SourceProfile(name=name, trust_score=initial_trust, tier=tier)
        self._sources[name] = profile
        return profile

    def get(self, name: str) -> Optional[SourceProfile]:
        return self._sources.get(name)

    def list_all(self) -> list[SourceProfile]:
        return list(self._sources.values())

    def list_primary(self) -> list[SourceProfile]:
        return [s for s in self._sources.values() if s.tier == "primary"]

    def get_trust(self, name: str) -> float:
        source = self._sources.get(name)
        return source.trust_score if source else 0.0

    # ── Scoring updates ──────────────────────────────────────────────────

    def record_accuracy(self, name: str, correct: int, total: int):
        """Record accuracy data point."""
        source = self._get_or_create(name)
        acc = correct / max(total, 1)
        source.accuracy_history.append(acc)
        if len(source.accuracy_history) > 100:
            source.accuracy_history = source.accuracy_history[-100:]
        self._recompute(name)

    def record_uptime(self, name: str, uptime_pct: float):
        source = self._get_or_create(name)
        source.uptime_history.append(uptime_pct)
        if len(source.uptime_history) > 100:
            source.uptime_history = source.uptime_history[-100:]
        self._recompute(name)

    def record_freshness(self, name: str, avg_age_days: float):
        source = self._get_or_create(name)
        source.freshness_avg_days = avg_age_days
        self._recompute(name)

    def record_completeness(self, name: str, completeness_pct: float):
        source = self._get_or_create(name)
        source.completeness_pct = completeness_pct
        self._recompute(name)

    def record_conflict(self, name: str, had_conflict: bool):
        source = self._get_or_create(name)
        source.conflict_total += 1
        if had_conflict:
            source.conflict_count += 1
        self._recompute(name)

    def record_latency(self, name: str, latency_ms: float):
        source = self._get_or_create(name)
        alpha = 0.1
        source.latency_avg_ms = (
            source.latency_avg_ms * (1 - alpha) + latency_ms * alpha
        )
        self._recompute(name)

    def mark_healthy(self, name: str):
        source = self._get_or_create(name)
        source.status = "healthy"
        source.last_validated = _dt.now(_tz.utc).isoformat()

    def mark_degraded(self, name: str):
        source = self._get_or_create(name)
        source.status = "degraded"
        source.last_validated = _dt.now(_tz.utc).isoformat()

    def mark_down(self, name: str):
        source = self._get_or_create(name)
        source.status = "down"
        source.last_validated = _dt.now(_tz.utc).isoformat()

    # ── Internal scoring ──────────────────────────────────────────────────

    def _recompute(self, name: str):
        source = self._sources.get(name)
        if not source:
            return

        # Accuracy score
        acc_score = (
            sum(source.accuracy_history) / len(source.accuracy_history)
            if source.accuracy_history else 0.5
        )

        # Uptime score
        uptime_score = (
            sum(source.uptime_history) / len(source.uptime_history)
            if source.uptime_history else 0.5
        )

        # Freshness score (1.0 = <1 day, 0.0 = >30 days)
        freshness_score = max(0.0, 1.0 - source.freshness_avg_days / 30)

        # Completeness score
        completeness_score = source.completeness_pct / 100

        # Conflict rate (1.0 = no conflicts, 0.0 = always conflicts).
        # No recorded conflicts = neutral evidence, not proof of perfection.
        conflict_score = (
            0.5 if source.conflict_total == 0 else
            1.0 - (source.conflict_count / max(source.conflict_total, 1))
        )

        # Latency score (1.0 = <100ms, 0.0 = >5000ms).
        # No latency data recorded = neutral evidence.
        latency_score = (
            0.5 if source.latency_avg_ms == 0 else
            max(0.0, 1.0 - source.latency_avg_ms / 5000)
        )

        # Weighted sum
        trust = (
            acc_score * self.WEIGHTS["accuracy"] +
            uptime_score * self.WEIGHTS["uptime"] +
            freshness_score * self.WEIGHTS["freshness"] +
            completeness_score * self.WEIGHTS["completeness"] +
            conflict_score * self.WEIGHTS["conflict_rate"] +
            latency_score * self.WEIGHTS["latency"]
        )
        source.trust_score = round(min(1.0, trust), 4)

        # Update tier
        for tier, threshold in sorted(self.TIER_THRESHOLDS.items(),
                                       key=lambda x: x[1], reverse=True):
            if trust >= threshold:
                source.tier = tier
                break
        else:
            source.tier = "unverified"

        # Update status recommendation
        if source.trust_score >= 0.75:
            source.status = "healthy"
        elif source.trust_score >= 0.50:
            source.status = "degraded"
        else:
            source.status = "down"

        source.recommendation = (
            "Primary source — use with confidence" if trust >= 0.75 else
            "Secondary source — verify critical fields" if trust >= 0.55 else
            "Low trust — manual review recommended" if trust >= 0.35 else
            "Source unreliable — consider disabling"
        )

        logger.info(f"Trust update [{name}]: score={trust:.3f}, tier={source.tier}")

    def _get_or_create(self, name: str) -> SourceProfile:
        if name not in self._sources:
            return self.register_source(name)
        return self._sources[name]

    # ── Dashboard ────────────────────────────────────────────────────────

    def get_dashboard(self) -> dict:
        return {
            "sources": [
                {
                    "name": s.name,
                    "trust_score": s.trust_score,
                    "tier": s.tier,
                    "status": s.status,
                    "accuracy": (
                        sum(s.accuracy_history) / len(s.accuracy_history)
                        if s.accuracy_history else 0.5
                    ),
                    "completeness_pct": s.completeness_pct,
                    "conflict_rate": (
                        s.conflict_count / max(s.conflict_total, 1)
                    ),
                    "recommendation": s.recommendation,
                }
                for s in self._sources.values()
            ],
            "primary_sources": [s.name for s in self.list_primary()],
            "total_sources": len(self._sources),
        }
