"""
Data Quality Engine — multi-dimensional quality scoring for every entity.

Scores completeness, freshness, consistency, accuracy, source confidence,
conflict detection, and produces an overall quality score (0-100).

Every score is EXPLAINED — no hardcoded values.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Quality Dimensions
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class QualityDimension:
    """A single quality dimension with score, explanation, and suggestions."""
    name: str
    score: float                # 0.0 — 1.0
    weight: float               # Contribution to overall score
    details: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class QualityReport:
    """Complete quality assessment for an entity."""
    entity_type: str
    entity_id: str
    overall_score: float        # 0-100, weighted sum of all dimensions
    dimensions: dict[str, QualityDimension]
    total_warnings: int
    total_suggestions: int
    sources_used: int
    quality_tier: str           # excellent, good, fair, poor, unknown
    scored_at: str = field(default="")
    scoring_version: int = 1

    def __post_init__(self):
        if not self.scored_at:
            self.scored_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "overall_score": self.overall_score,
            "quality_tier": self.quality_tier,
            "dimensions": {
                k: {"score": round(v.score * 100, 1), "warnings": v.warnings}
                for k, v in self.dimensions.items()
            },
            "warnings": self.total_warnings,
            "suggestions": self.total_suggestions,
            "sources": self.sources_used,
            "scored_at": self.scored_at,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Quality Scorers — one per dimension
# ═══════════════════════════════════════════════════════════════════════════

class CompletenessScorer:
    """Score how many expected fields are present and non-empty."""

    def score(self, entity: dict, required: list[str], optional: list[str]) -> QualityDimension:
        total = len(required) + len(optional)
        present = 0
        warnings = []

        for field in required:
            if entity.get(field) not in (None, "", 0, []):
                present += 1
            else:
                warnings.append(f"Missing required field: {field}")

        for field in optional:
            if entity.get(field) not in (None, "", 0, []):
                present += 1

        score = present / max(total, 1)
        return QualityDimension(
            name="completeness",
            score=score,
            weight=0.25,
            details={"required_fields": len(required), "filled": present, "total": total},
            warnings=warnings,
            suggestions=["Fill missing required fields"] if warnings else [],
        )


class FreshnessScorer:
    """Score how recently data was updated. Older data gets lower scores."""

    def score(self, entity: dict, updated_field: str = "updated_at",
              max_age_days: int = 30) -> QualityDimension:
        updated = entity.get(updated_field)
        if not updated:
            return QualityDimension(
                name="freshness", score=0.0, weight=0.15,
                warnings=["No update timestamp"],
                suggestions=["Ensure sync updates timestamp"],
            )

        try:
            if isinstance(updated, str):
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            else:
                updated_dt = updated
            age_days = (datetime.now(timezone.utc) - updated_dt.replace(tzinfo=timezone.utc)).days
        except (ValueError, TypeError):
            return QualityDimension(name="freshness", score=0.0, weight=0.15,
                                     warnings=["Invalid timestamp format"])

        if age_days <= 1:
            score = 1.0
        elif age_days <= 7:
            score = 0.9
        elif age_days <= 14:
            score = 0.7
        elif age_days <= max_age_days:
            score = 0.5
        else:
            score = max(0.1, 1.0 - (age_days / (max_age_days * 3)))

        return QualityDimension(
            name="freshness",
            score=score,
            weight=0.15,
            details={"age_days": age_days},
            warnings=[f"Data is {age_days} days old"] if age_days > 14 else [],
            suggestions=["Schedule a refresh"] if age_days > 14 else [],
        )


class ConsistencyScorer:
    """Score internal consistency — e.g., record matches fight results."""

    def score(self, entity: dict, checks: list[tuple[str, Callable[[dict], tuple[bool, str]]]]) -> QualityDimension:
        passed = 0
        warnings = []
        for name, check_fn in checks:
            ok, msg = check_fn(entity)
            if ok:
                passed += 1
            else:
                warnings.append(f"{name}: {msg}")

        total = len(checks) if checks else 1
        score = passed / total
        return QualityDimension(
            name="consistency",
            score=score,
            weight=0.20,
            details={"checks_total": total, "checks_passed": passed},
            warnings=warnings,
            suggestions=["Review inconsistent data"] if warnings else [],
        )


class AccuracyScorer:
    """Score accuracy by comparing against multiple sources."""

    def score(self, entity: dict, source_values: dict[str, Any]) -> QualityDimension:
        if len(source_values) < 2:
            return QualityDimension(
                name="accuracy", score=0.5, weight=0.25,
                warnings=["Only one source available"],
                suggestions=["Add more data sources"],
            )

        agreements = 0
        conflicts = 0
        for field, values in source_values.items():
            unique = set(str(v) for v in values if v is not None)
            if len(unique) <= 1:
                agreements += 1
            else:
                conflicts += 1

        total = max(len(source_values), 1)
        score = agreements / total

        return QualityDimension(
            name="accuracy",
            score=score,
            weight=0.25,
            details={
                "sources_compared": len(source_values),
                "fields_agreed": agreements,
                "fields_conflicted": conflicts,
            },
            warnings=[f"{conflicts} fields have conflicting values"] if conflicts else [],
            suggestions=["Resolve source conflicts"] if conflicts else [],
        )


class SourceConfidenceScorer:
    """Score based on source reliability trust scores."""

    def score(self, entity: dict, source_trust: dict[str, float]) -> QualityDimension:
        if not source_trust:
            return QualityDimension(
                name="source_confidence", score=0.3, weight=0.15,
                warnings=["No source trust data available"],
            )

        scores = list(source_trust.values())
        avg_trust = sum(scores) / len(scores)
        result = QualityDimension(
            name="source_confidence",
            score=avg_trust,
            weight=0.15,
            details={"sources": len(scores), "avg_trust": round(avg_trust, 3)},
        )
        if avg_trust < 0.5:
            result.warnings.append(f"Low source trust: {avg_trust:.2f}")
            result.suggestions.append("Use higher-trust sources")
        return result


# ═══════════════════════════════════════════════════════════════════════════
# Quality Engine
# ═══════════════════════════════════════════════════════════════════════════

class QualityEngine:
    """Orchestrates quality scoring across all dimensions."""

    TIER_THRESHOLDS = {
        "excellent": 85, "good": 70, "fair": 50, "poor": 25,
    }

    def __init__(self):
        self.completeness = CompletenessScorer()
        self.freshness = FreshnessScorer()
        self.consistency = ConsistencyScorer()
        self.accuracy = AccuracyScorer()
        self.source_confidence = SourceConfidenceScorer()
        self._history: list[QualityReport] = []

    def assess_fighter(
        self,
        fighter: dict,
        source_trust: dict[str, float] | None = None,
        source_values: dict[str, Any] | None = None,
    ) -> QualityReport:
        """Full quality assessment for a fighter."""
        dims = {}

        dims["completeness"] = self.completeness.score(fighter, required=[
            "first_name", "last_name", "wins", "losses",
        ], optional=[
            "nickname", "height_cm", "weight_kg", "reach_cm",
            "nationality", "birth_date", "stance", "fighting_style",
        ])

        dims["freshness"] = self.freshness.score(fighter)

        dims["consistency"] = self.consistency.score(fighter, checks=[
            ("record_positive", lambda f: (
                f.get("wins", 0) >= 0 and f.get("losses", 0) >= 0,
                "Negative record values")),
            ("height_range", lambda f: (
                not f.get("height_cm") or 120 <= f["height_cm"] <= 220,
                f"Height out of range: {f.get('height_cm')}")),
            ("weight_range", lambda f: (
                not f.get("weight_kg") or 45 <= f["weight_kg"] <= 150,
                f"Weight out of range: {f.get('weight_kg')}")),
        ])

        dims["accuracy"] = self.accuracy.score(fighter, source_values or {})

        dims["source_confidence"] = self.source_confidence.score(
            fighter, source_trust or {},
        )

        return self._assemble("fighter", fighter.get("canonical_id", str(fighter)[:50]),
                              dims, len(source_trust or {}))

    def assess_event(
        self, event: dict, source_trust: dict[str, float] | None = None,
    ) -> QualityReport:
        """Full quality assessment for an event."""
        dims = {}
        dims["completeness"] = self.completeness.score(event, required=[
            "name", "date_utc",
        ], optional=["venue", "city", "country", "promotion", "fight_count"])

        dims["freshness"] = self.freshness.score(event)

        dims["consistency"] = self.consistency.score(event, checks=[
            ("date_valid", lambda e: (bool(e.get("date_utc")), "Missing date")),
        ])

        dims["accuracy"] = self.accuracy.score(event, {})
        dims["source_confidence"] = self.source_confidence.score(
            event, source_trust or {},
        )
        return self._assemble("event", event.get("canonical_id", str(event)[:50]),
                              dims, len(source_trust or {}))

    def _assemble(
        self, entity_type: str, entity_id: str,
        dimensions: dict[str, QualityDimension], sources: int,
    ) -> QualityReport:
        overall = sum(d.score * d.weight for d in dimensions.values()) * 100

        tier = "unknown"
        for name, threshold in sorted(self.TIER_THRESHOLDS.items(),
                                       key=lambda x: x[1], reverse=True):
            if overall >= threshold:
                tier = name
                break
        if tier == "unknown" and overall > 0:
            tier = "poor"

        report = QualityReport(
            entity_type=entity_type,
            entity_id=entity_id,
            overall_score=round(overall, 1),
            dimensions=dimensions,
            total_warnings=sum(len(d.warnings) for d in dimensions.values()),
            total_suggestions=sum(len(d.suggestions) for d in dimensions.values()),
            sources_used=sources,
            quality_tier=tier,
        )
        self._history.append(report)
        if len(self._history) > 1000:
            self._history = self._history[-1000:]
        return report

    def get_dashboard(self) -> dict:
        """Aggregate quality metrics across all assessments."""
        if not self._history:
            return {"status": "no_data"}
        recent = self._history[-100:]
        scores = [r.overall_score for r in recent]
        tiers = {}
        for r in recent:
            tiers[r.quality_tier] = tiers.get(r.quality_tier, 0) + 1
        return {
            "total_assesments": len(self._history),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "tier_distribution": tiers,
            "avg_warnings": round(sum(r.total_warnings for r in recent) / len(recent), 1),
        }
