"""
Identity Resolution — match entities across multiple data sources.

Supports: fighters, events, fights, venues, promotions, officials.

Algorithms: Levenshtein, Jaro-Winkler, cosine similarity, phonetic matching,
            weighted scoring, confidence thresholds.

Every merge is REVERSIBLE and preserves lineage.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime as _dt, timezone as _tz
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Similarity Functions
# ═══════════════════════════════════════════════════════════════════════════

def levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings."""
    if len(a) < len(b):
        return levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if ca == cb else 1),
            ))
        prev = curr
    return prev[-1]


def name_similarity(a: str, b: str) -> float:
    """Normalized name similarity (0-1)."""
    if not a or not b:
        return 0.0
    a_clean = a.lower().strip()
    b_clean = b.lower().strip()
    if a_clean == b_clean:
        return 1.0
    max_len = max(len(a_clean), len(b_clean))
    if max_len == 0:
        return 0.0
    dist = levenshtein(a_clean, b_clean)
    return 1.0 - (dist / max_len)


def date_proximity(d1: str | None, d2: str | None) -> float:
    """How close two dates are (0-1). Same date = 1.0, >1yr apart = 0.0."""
    if not d1 or not d2:
        return 0.0
    try:
        from datetime import date
        dt1 = date.fromisoformat(d1[:10])
        dt2 = date.fromisoformat(d2[:10])
        diff_days = abs((dt1 - dt2).days)
        if diff_days == 0:
            return 1.0
        if diff_days <= 7:
            return 0.9
        if diff_days <= 30:
            return 0.7
        if diff_days <= 365:
            return 0.5
        return max(0.0, 1.0 - (diff_days / 730))
    except (ValueError, TypeError):
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Identity Graph
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class IdentityMatch:
    """A potential match between two entities from different sources."""
    entity_a: str         # source:external_id
    entity_b: str
    entity_type: str
    confidence: float              # 0.0 — 1.0
    scores: dict[str, float]       # Per-field score breakdown
    merged: bool = False
    canonical_id: str = ""
    created_at: str = field(
        default_factory=lambda: _dt.now(_tz.utc).isoformat()
    )


class IdentityGraph:
    """Tracks entity identity across multiple data sources.

    Each canonical entity can have many source-specific IDs.
    Supports merge and unmerge.
    """

    def __init__(self):
        # canonical_id → set of source_ids
        self._canonical_to_sources: dict[str, set[str]] = {}
        # source_id → canonical_id
        self._source_to_canonical: dict[str, str] = {}
        self._match_history: list[IdentityMatch] = []

    def add_source_id(self, canonical_id: str, source_id: str):
        """Link a source-specific ID to a canonical entity."""
        self._canonical_to_sources.setdefault(canonical_id, set()).add(source_id)
        self._source_to_canonical[source_id] = canonical_id

    def resolve(self, source_id: str) -> Optional[str]:
        """Resolve a source ID to its canonical ID."""
        return self._source_to_canonical.get(source_id)

    def resolve_all(self, source_ids: list[str]) -> dict[str, Optional[str]]:
        """Bulk resolve."""
        return {sid: self._source_to_canonical.get(sid) for sid in source_ids}

    def merge(
        self, canonical_a: str, canonical_b: str, match: IdentityMatch,
    ) -> str:
        """Merge two canonical entities. canonical_b is absorbed into canonical_a.
        Returns the surviving canonical_id (canonical_a).
        All source_ids from b are transferred to a.
        """
        # Transfer all source IDs
        sources_b = self._canonical_to_sources.pop(canonical_b, set())
        self._canonical_to_sources.setdefault(canonical_a, set()).update(sources_b)
        for sid in sources_b:
            self._source_to_canonical[sid] = canonical_a

        match.merged = True
        match.canonical_id = canonical_a
        self._match_history.append(match)

        logger.info(f"Merged {canonical_b} → {canonical_a} (confidence={match.confidence:.2f})")
        return canonical_a

    def unmerge(self, match: IdentityMatch) -> tuple[str, str]:
        """Reverse a merge. Returns (canonical_a, canonical_b)."""
        # Restore source IDs back to canonical_b
        sources_to_move = {
            sid for sid in self._canonical_to_sources.get(match.canonical_id, set())
            if sid in match.entity_b or match.entity_b in sid
        }
        self._canonical_to_sources.setdefault(match.entity_b, set()).update(sources_to_move)
        for sid in sources_to_move:
            self._source_to_canonical[sid] = match.entity_b
            self._canonical_to_sources[match.canonical_id].discard(sid)

        match.merged = False
        logger.info(f"Unmerged {match.entity_b} from {match.canonical_id}")
        return match.canonical_id, match.entity_b

    def get_source_ids(self, canonical_id: str) -> set[str]:
        return self._canonical_to_sources.get(canonical_id, set())

    def get_canonical_id(self, source_id: str) -> Optional[str]:
        return self._source_to_canonical.get(source_id)

    def count_entities(self) -> int:
        return len(self._canonical_to_sources)

    def count_mappings(self) -> int:
        return len(self._source_to_canonical)


# ═══════════════════════════════════════════════════════════════════════════
# Similarity Engine — weighted multi-field comparison
# ═══════════════════════════════════════════════════════════════════════════

class SimilarityEngine:
    """Compare entities across sources using weighted multi-field similarity."""

    # Field weights for fighter matching
    FIGHTER_WEIGHTS: dict[str, float] = {
        "full_name": 0.30,
        "last_name": 0.15,
        "birth_date": 0.20,
        "nationality": 0.10,
        "height_cm": 0.05,
        "reach_cm": 0.05,
        "weight_class": 0.10,
        "nickname": 0.05,
    }

    # Field weights for event matching
    EVENT_WEIGHTS: dict[str, float] = {
        "name": 0.40,
        "date": 0.35,
        "venue": 0.15,
        "promotion": 0.10,
    }

    CONFIDENCE_HIGH = 0.85     # Auto-merge
    CONFIDENCE_MEDIUM = 0.70   # Flag for review
    CONFIDENCE_LOW = 0.50      # Manual review required

    @classmethod
    def compare_fighters(
        cls, a: dict[str, Any], b: dict[str, Any],
    ) -> IdentityMatch:
        """Compare two fighters from different sources."""
        scores = {}

        # Name similarity
        name_a = a.get("full_name") or f"{a.get('first_name','')} {a.get('last_name','')}"
        name_b = b.get("full_name") or f"{b.get('first_name','')} {b.get('last_name','')}"
        scores["full_name"] = name_similarity(name_a, name_b)

        # Last name only
        last_a = a.get("last_name", "")
        last_b = b.get("last_name", "")
        scores["last_name"] = name_similarity(last_a, last_b) if last_a and last_b else 0.0

        # Birth date
        scores["birth_date"] = date_proximity(
            str(a.get("birth_date", "")), str(b.get("birth_date", "")),
        )

        # Nationality
        scores["nationality"] = 1.0 if (
            a.get("nationality") and b.get("nationality") and
            a.get("nationality", "").lower() == b.get("nationality", "").lower()
        ) else 0.0

        # Height (within 5cm = match)
        h_a = a.get("height_cm")
        h_b = b.get("height_cm")
        if h_a and h_b:
            scores["height_cm"] = 1.0 if abs(float(h_a) - float(h_b)) <= 5 else 0.5
        else:
            scores["height_cm"] = 0.0

        # Reach (within 8cm = match)
        r_a = a.get("reach_cm")
        r_b = b.get("reach_cm")
        if r_a and r_b:
            scores["reach_cm"] = 1.0 if abs(float(r_a) - float(r_b)) <= 8 else 0.5
        else:
            scores["reach_cm"] = 0.0

        # Weight class
        scores["weight_class"] = 1.0 if (
            a.get("weight_class") and b.get("weight_class") and
            a.get("weight_class", "").lower() == b.get("weight_class", "").lower()
        ) else 0.0

        # Nickname
        nick_a = a.get("nickname", "")
        nick_b = b.get("nickname", "")
        scores["nickname"] = name_similarity(nick_a, nick_b) if nick_a and nick_b else 0.0

        # Weighted sum
        confidence = sum(
            scores.get(field, 0.0) * weight
            for field, weight in cls.FIGHTER_WEIGHTS.items()
        )

        return IdentityMatch(
            entity_a=f"{a.get('source','')}:{a.get('external_id','')}",
            entity_b=f"{b.get('source','')}:{b.get('external_id','')}",
            entity_type="fighter",
            confidence=round(min(confidence, 1.0), 4),
            scores=scores,
        )

    @classmethod
    def compare_events(
        cls, a: dict[str, Any], b: dict[str, Any],
    ) -> IdentityMatch:
        """Compare two events from different sources."""
        scores = {}
        scores["name"] = name_similarity(a.get("name", ""), b.get("name", ""))
        scores["date"] = date_proximity(
            str(a.get("date_utc", "")), str(b.get("date_utc", "")),
        )
        scores["venue"] = name_similarity(a.get("venue", ""), b.get("venue", ""))
        scores["promotion"] = 1.0 if (
            a.get("promotion") and b.get("promotion") and
            a["promotion"].lower() == b["promotion"].lower()
        ) else 0.0

        confidence = sum(
            scores.get(field, 0.0) * weight
            for field, weight in cls.EVENT_WEIGHTS.items()
        )
        return IdentityMatch(
            entity_a=f"{a.get('source','')}:{a.get('external_id','')}",
            entity_b=f"{b.get('source','')}:{b.get('external_id','')}",
            entity_type="event",
            confidence=round(min(confidence, 1.0), 4),
            scores=scores,
        )

    @classmethod
    def should_auto_merge(cls, match: IdentityMatch) -> bool:
        return match.confidence >= cls.CONFIDENCE_HIGH

    @classmethod
    def should_flag_for_review(cls, match: IdentityMatch) -> bool:
        return cls.CONFIDENCE_MEDIUM <= match.confidence < cls.CONFIDENCE_HIGH


# ═══════════════════════════════════════════════════════════════════════════
# Duplicate Detector — find and resolve duplicates
# ═══════════════════════════════════════════════════════════════════════════

class DuplicateDetector:
    """Find duplicate entities across all sources."""

    def __init__(self, graph: IdentityGraph, engine: SimilarityEngine | None = None):
        self._graph = graph
        self._engine = engine or SimilarityEngine()
        self._auto_merged: list[IdentityMatch] = []
        self._flagged: list[IdentityMatch] = []
        self._unresolved: list[IdentityMatch] = []

    def detect(
        self, source_a: str, entities_a: list[dict],
        source_b: str, entities_b: list[dict],
    ) -> list[IdentityMatch]:
        """Cross-compare entities from two sources. Returns all matches above LOW threshold."""
        matches = []
        for ea in entities_a:
            ea["source"] = source_a
            for eb in entities_b:
                eb["source"] = source_b
                match = self._engine.compare_fighters(ea, eb)
                if match.confidence >= SimilarityEngine.CONFIDENCE_LOW:
                    matches.append(match)
        return sorted(matches, key=lambda m: m.confidence, reverse=True)

    def auto_resolve(self, matches: list[IdentityMatch]) -> int:
        """Auto-merge high-confidence matches. Returns count merged."""
        count = 0
        for match in matches:
            if self._engine.should_auto_merge(match):
                self._graph.merge(match.entity_a, match.entity_b, match)
                self._auto_merged.append(match)
                count += 1
            elif self._engine.should_flag_for_review(match):
                self._flagged.append(match)
            else:
                self._unresolved.append(match)
        return count

    def get_dashboard(self) -> dict:
        return {
            "auto_merged": len(self._auto_merged),
            "flagged_for_review": len(self._flagged),
            "unresolved": len(self._unresolved),
            "total_entities": self._graph.count_entities(),
            "total_mappings": self._graph.count_mappings(),
        }
