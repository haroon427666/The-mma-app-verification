"""Scoring signals — decomposable recommendation scores.

Every recommendation gets 8 scores that combine into a final ranking.
Each scorer returns [0,1] with optional explanation.
"""

import numpy as np
import math
from typing import Any, Optional


class ScoreResult:
    def __init__(self, score: float, explanation: str = ""):
        self.score = min(max(score, 0.0), 1.0)
        self.explanation = explanation


def personalization_score(
    profile: Any, entity: dict, weight: float,
) -> ScoreResult:
    """How well does this entity match the user's profile?"""
    reasons = []
    s = 0.0

    wc = entity.get("weight_class", "")
    if wc and hasattr(profile, "_weight_class_affinity"):
        aff = profile._weight_class_affinity.get(wc, 0)
        if aff > 0.05:
            s += aff * 0.4
            reasons.append(f"follows {wc}")

    style = entity.get("style_vector")
    if style is not None and hasattr(profile, "style_vector"):
        pv = profile._style_affinity if hasattr(profile, "_style_affinity") else profile.style_vector
        sv = np.array(style, dtype=np.float32)
        sim = float(np.dot(pv / (np.linalg.norm(pv) + 1e-10), sv / (np.linalg.norm(sv) + 1e-10)))
        if sim > 0.3:
            s += sim * 0.3
            reasons.append("style match")

    fid = entity.get("fighter_id", entity.get("id", ""))
    if hasattr(profile, "_fighter_affinity"):
        fighter_aff = profile._fighter_affinity.get(fid, 0)
        if fighter_aff > 0:
            s += fighter_aff * 0.3
            reasons.append("previously engaged")

    return ScoreResult(s, ", ".join(reasons))


def similarity_score(
    source_entity: dict, candidate: dict, weight: float,
    vector_store: Any = None,
) -> ScoreResult:
    """How similar is this candidate to entities the user already likes?"""
    if vector_store is None:
        return ScoreResult(0.5)
    source_emb = source_entity.get("embedding")
    cand_emb = candidate.get("embedding")
    if source_emb is None or cand_emb is None:
        return ScoreResult(0.5)
    sim = float(np.dot(np.array(source_emb), np.array(cand_emb)))
    tag = "highly similar" if sim > 0.85 else "similar" if sim > 0.7 else ""
    return ScoreResult(sim, tag)


def trending_score(entity: dict, trending_data: dict, weight: float) -> ScoreResult:
    """Is this entity trending right now?"""
    eid = entity.get("id", "")
    td = trending_data.get(eid, {})
    velocity = td.get("velocity", 0)
    if velocity > 2:
        return ScoreResult(min(velocity / 10.0, 1.0), "trending fast")
    if velocity > 0.5:
        return ScoreResult(0.3, "rising")
    return ScoreResult(0.0)


def popularity_score(entity: dict, weight: float) -> ScoreResult:
    """Raw popularity — views, favorites, watchlist count."""
    views = entity.get("views", 0)
    favs = entity.get("favorites_count", 0)
    score = min(views / 10000.0, 0.4) + min(favs / 500.0, 0.3) + 0.3
    return ScoreResult(min(score, 1.0), f"{views} views" if views > 100 else "")


def freshness_score(entity: dict, weight: float, half_life_days: float = 30) -> ScoreResult:
    """How new/relevant is this content?"""
    days = entity.get("days_since_event", entity.get("days_until_event", 0))
    if days is None:
        return ScoreResult(0.5)
    score = math.exp(-days * math.log(2) / half_life_days)
    tag = ""
    if days < 0 and abs(days) < 7:
        tag = f"in {-days} days"
    elif days < 3:
        tag = "just happened"
    return ScoreResult(score, tag)


def quality_score(entity: dict, weight: float) -> ScoreResult:
    """How good is this fight/event based on objective metrics?"""
    elo = entity.get("elo_rating", 1500)
    championship = entity.get("championship_score", 0)
    finish_rate = entity.get("finish_rate", 0.5)
    is_title = entity.get("is_title_fight", False)

    s = (elo - 1300) / 600.0 * 0.3
    s += championship * 0.3
    s += finish_rate * 0.2
    s += 0.2 if is_title else 0.0

    tags = []
    if is_title: tags.append("title fight")
    if elo > 1700: tags.append("elite matchup")

    return ScoreResult(min(s, 1.0), ", ".join(tags))


def diversity_penalty(
    candidate: dict, already_recommended: list[dict], weight: float,
) -> ScoreResult:
    """Penalize if candidate is too similar to already-recommended items."""
    if not already_recommended:
        return ScoreResult(0.0)
    cand_emb = np.array(candidate.get("embedding", np.zeros(64)), dtype=np.float32)
    cn = np.linalg.norm(cand_emb) + 1e-10
    max_sim = 0.0
    for item in already_recommended[-3:]:
        item_emb = np.array(item.get("embedding", np.zeros(64)), dtype=np.float32)
        inorm = np.linalg.norm(item_emb) + 1e-10
        sim = float(np.dot(cand_emb / cn, item_emb / inorm))
        max_sim = max(max_sim, sim)
    penalty = max(0, (max_sim - 0.5) * 2.0) * weight
    return ScoreResult(penalty, "similar to previous" if penalty > 0.3 else "")


def novelty_bonus(entity: dict, user_seen_ids: set[str], weight: float) -> ScoreResult:
    """Reward entities the user hasn't seen."""
    eid = entity.get("id", "")
    if eid not in user_seen_ids:
        return ScoreResult(0.3, "new to you")
    return ScoreResult(0.0)


# ── Final Score Aggregator ────────────────────────────────────────────────

def compute_final_score(
    profile: Any, entity: dict, trending_data: dict,
    user_seen_ids: set[str], source_entity: dict | None = None,
    already_recommended: list[dict] | None = None,
) -> tuple[float, list[str]]:
    """Compute the final recommendation score with all signals and explanations."""

    already = already_recommended or []
    source = source_entity or {}

    signals = [
        ("personalization", personalization_score(profile, entity, 0.30)),
        ("similarity", similarity_score(source, entity, 0.15)),
        ("trending", trending_score(entity, trending_data, 0.10)),
        ("popularity", popularity_score(entity, 0.08)),
        ("freshness", freshness_score(entity, 0.12)),
        ("quality", quality_score(entity, 0.10)),
    ]

    total = sum(s.score * 0.1 for _, s in signals)
    total -= diversity_penalty(entity, already, 0.05).score
    total += novelty_bonus(entity, user_seen_ids, 0.05).score

    reasons = [s.explanation for _, s in signals if s.explanation]
    if entity.get("is_watchlist"):
        total += 0.15
        reasons.append("on your watchlist")

    return min(max(total, 0.0), 1.0), reasons
