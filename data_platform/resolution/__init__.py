"""
Entity Resolution & Deduplication — production merging across sources.

Extends platform.identity with: canonical merge pipeline, alias database,
image similarity metadata, conflict reports, full audit history.

Every merge is EXPLAINABLE and REVERSIBLE.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime as _dt, timezone as _tz
from typing import Any, Optional

from data_platform.identity import (
    SimilarityEngine, IdentityGraph, IdentityMatch,
    name_similarity, date_proximity,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Alias Database — nickname + alternate name resolution
# ═══════════════════════════════════════════════════════════════════════════

class AliasDatabase:
    """Maps known aliases/nicknames to canonical names."""

    def __init__(self):
        self._aliases: dict[str, str] = {}

    def add(self, alias: str, canonical: str):
        self._aliases[alias.lower().strip()] = canonical.lower().strip()

    def resolve(self, name: str) -> str:
        return self._aliases.get(name.lower().strip(), name)

    def is_alias(self, name: str) -> bool:
        return name.lower().strip() in self._aliases

    def count(self) -> int:
        return len(self._aliases)


# ═══════════════════════════════════════════════════════════════════════════
# Merge Audit — every merge tracked with full history
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MergeRecord:
    """Immutable record of a merge operation."""
    id: str
    entity_type: str
    survivor_id: str
    absorbed_id: str
    confidence: float
    scores: dict[str, float]
    rationale: str
    merged_at: str = ""
    merged_by: str = "auto"
    reversible: bool = True

    def __post_init__(self):
        if not self.merged_at:
            self.merged_at = _dt.now(_tz.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "entity_type": self.entity_type,
            "survivor": self.survivor_id, "absorbed": self.absorbed_id,
            "confidence": self.confidence, "rationale": self.rationale,
            "merged_at": self.merged_at, "reversible": self.reversible,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Resolution Engine — orchestrate cross-source merging
# ═══════════════════════════════════════════════════════════════════════════

class ResolutionEngine:
    """Complete entity resolution pipeline.

    Pipeline: entities → compare → score → cluster → merge → audit
    """

    def __init__(self, graph: IdentityGraph | None = None):
        self._graph = graph or IdentityGraph()
        self._aliases = AliasDatabase()
        self._merge_history: list[MergeRecord] = []
        self._engine = SimilarityEngine()
        self._auto_merged_count = 0
        self._manual_flagged_count = 0

    # ── Alias management ─────────────────────────────────────────────────

    def register_alias(self, alias: str, canonical: str):
        self._aliases.add(alias, canonical)

    def resolve_alias(self, name: str) -> str:
        return self._aliases.resolve(name)

    # ── Cross-source resolution ──────────────────────────────────────────

    def resolve_fighters(
        self, source_a: str, fighters_a: list[dict],
        source_b: str, fighters_b: list[dict],
    ) -> dict:
        """Cross-compare fighters from two sources, auto-merge high-confidence matches."""
        matches = []
        auto_merged = 0
        flagged = 0

        for fa in fighters_a:
            # Resolve aliases first
            fa["full_name"] = self._aliases.resolve(
                fa.get("full_name") or f"{fa.get('first_name','')} {fa.get('last_name','')}"
            )
            fa["source"] = source_a

            for fb in fighters_b:
                fb["full_name"] = self._aliases.resolve(
                    fb.get("full_name") or f"{fb.get('first_name','')} {fb.get('last_name','')}"
                )
                fb["source"] = source_b

                match = self._engine.compare_fighters(fa, fb)

                if match.confidence < SimilarityEngine.CONFIDENCE_LOW:
                    continue

                matches.append(match)

                # Auto-merge high confidence
                if self._engine.should_auto_merge(match):
                    entity_a = f"{source_a}:{fa.get('external_id', fa.get('canonical_id',''))}"
                    entity_b = f"{source_b}:{fb.get('external_id', fb.get('canonical_id',''))}"
                    survivor = self._graph.merge(entity_a, entity_b, match)
                    auto_merged += 1
                    self._auto_merged_count += 1

                    record = MergeRecord(
                        id=f"merge-{_dt.now(_tz.utc).timestamp()}",
                        entity_type="fighter",
                        survivor_id=survivor,
                        absorbed_id=entity_b,
                        confidence=match.confidence,
                        scores=match.scores,
                        rationale=self._build_rationale(match),
                    )
                    self._merge_history.append(record)

                elif self._engine.should_flag_for_review(match):
                    flagged += 1
                    self._manual_flagged_count += 1

        return {
            "total_comparisons": len(fighters_a) * len(fighters_b),
            "matches_found": len(matches),
            "auto_merged": auto_merged,
            "flagged_for_review": flagged,
            "high_confidence": [m for m in matches if m.confidence >= 0.85],
        }

    # ── Cluster detection ────────────────────────────────────────────────

    def find_duplicate_clusters(
        self, entities: list[dict], threshold: float = 0.85,
    ) -> list[list[dict]]:
        """Group entities into duplicate clusters using pairwise similarity."""
        clusters: list[list[dict]] = []
        assigned: set[int] = set()

        for i, ea in enumerate(entities):
            if i in assigned:
                continue
            cluster = [ea]
            assigned.add(i)

            for j, eb in enumerate(entities):
                if j in assigned or i == j:
                    continue
                match = self._engine.compare_fighters(ea, eb)
                if match.confidence >= threshold:
                    cluster.append(eb)
                    assigned.add(j)

            clusters.append(cluster)

        return clusters

    # ── Rationale generation ─────────────────────────────────────────────

    def _build_rationale(self, match: IdentityMatch) -> str:
        parts = []
        for field, score in sorted(match.scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 0.9:
                parts.append(f"{field}: exact match")
            elif score >= 0.7:
                parts.append(f"{field}: close match ({score:.0%})")
            elif score >= 0.5:
                parts.append(f"{field}: partial match ({score:.0%})")
        return f"Auto-merged at {match.confidence:.0%} confidence. " + "; ".join(parts[:5])

    # ── Audit & Dashboard ────────────────────────────────────────────────

    def get_merge_history(self, limit: int = 50) -> list[dict]:
        return [m.to_dict() for m in self._merge_history[-limit:]]

    def get_dashboard(self) -> dict:
        return {
            "total_entities": self._graph.count_entities(),
            "total_mappings": self._graph.count_mappings(),
            "auto_merged": self._auto_merged_count,
            "flagged_for_review": self._manual_flagged_count,
            "aliases_registered": self._aliases.count(),
            "merge_history_length": len(self._merge_history),
        }

    def reverse_merge(self, merge_id: str) -> Optional[tuple[str, str]]:
        """Reverse a merge by replaying the inverse."""
        for record in self._merge_history:
            if record.id == merge_id and record.reversible:
                return self._graph.unmerge(
                    IdentityMatch(
                        entity_a=record.survivor_id,
                        entity_b=record.absorbed_id,
                        entity_type=record.entity_type,
                        confidence=record.confidence,
                        scores=record.scores,
                    )
                )
        return None
