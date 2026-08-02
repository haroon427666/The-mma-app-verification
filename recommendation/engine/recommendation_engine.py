"""Recommendation Engine — the main orchestrator.

Pipeline:
    User Activity → UserProfile → Candidates → Filter → Score → Rerank → Diversify → Explain → Return
"""

import numpy as np
from typing import Any, Optional

from recommendation.user_profile.builder import UserProfileBuilder, UserProfile
from recommendation.scoring.final_score import compute_final_score


class RecommendationResult:
    def __init__(self, entity: dict, score: float, reasons: list[str]):
        self.entity = entity
        self.score = score
        self.reasons = reasons

    def to_dict(self) -> dict:
        return {
            "id": self.entity.get("id", ""),
            "name": self.entity.get("name", self.entity.get("full_name", "")),
            "type": self.entity.get("type", "fighter"),
            "score": round(self.score, 3),
            "reasons": self.reasons,
            "image_url": self.entity.get("image_url", self.entity.get("headshot_url", "")),
            "weight_class": self.entity.get("weight_class", ""),
            "record": self.entity.get("record", ""),
        }


class RecommendationEngine:
    """Production recommendation pipeline — nothing hardcoded, every step measurable."""

    def __init__(
        self,
        vector_store: Any = None,
        trending_data: dict | None = None,
    ):
        self.profile_builder = UserProfileBuilder()
        self.vector_store = vector_store
        self.trending_data = trending_data or {}
        self._seen: dict[str, set[str]] = {}

    def recommend(
        self,
        user_id: str,
        interactions: list[dict],
        candidates: list[dict],
        k: int = 20,
        source_entity: dict | None = None,
        exclude_ids: set[str] | None = None,
    ) -> list[RecommendationResult]:
        """Generate personalized recommendations.

        Args:
            user_id: Unique user identifier
            interactions: User's activity history [{type, weight, entity}, ...]
            candidates: Pool of entities to recommend from
            k: Number of recommendations to return
            source_entity: Entity that triggered this (for "because you viewed X")
            exclude_ids: IDs to exclude (already dismissed, etc.)
        """
        # 1. Build user profile
        profile = self.profile_builder.build(user_id, interactions)

        # 2. Filter excluded
        exclude = exclude_ids or set()
        seen = self._seen.get(user_id, set())
        candidates = [c for c in candidates if c.get("id", "") not in exclude and c.get("id", "") not in seen]

        # 3. Score every candidate
        scored = []
        for candidate in candidates:
            score, reasons = compute_final_score(
                profile, candidate, self.trending_data,
                seen, source_entity, [s.entity for s in scored],
            )
            scored.append(RecommendationResult(candidate, score, reasons))

        # 4. Sort by score
        scored.sort(key=lambda r: r.score, reverse=True)

        # 5. Diversity re-ranking: penalize consecutive similar items
        reranked = self._rerank_diverse(scored)

        # 6. Track seen
        if user_id not in self._seen:
            self._seen[user_id] = set()
        for r in reranked[:k]:
            self._seen[user_id].add(r.entity.get("id", ""))

        return reranked[:k]

    def recommend_from_source(
        self,
        user_id: str,
        interactions: list[dict],
        source_entity: dict,
        candidate_pool: list[dict],
        k: int = 10,
    ) -> list[RecommendationResult]:
        """Recommend 'because you viewed/followed X'."""
        # Boost candidates similar to source
        source_emb = np.array(source_entity.get("embedding", np.zeros(64)), dtype=np.float32)
        for c in candidate_pool:
            cand_emb = np.array(c.get("embedding", np.zeros(64)), dtype=np.float32)
            sim = float(np.dot(source_emb / (np.linalg.norm(source_emb) + 1e-10),
                              cand_emb / (np.linalg.norm(cand_emb) + 1e-10)))
            c["_source_similarity"] = sim

        return self.recommend(user_id, interactions, candidate_pool, k=k, source_entity=source_entity)

    def _rerank_diverse(self, results: list[RecommendationResult]) -> list[RecommendationResult]:
        """Re-rank to avoid showing too-similar items consecutively."""
        if len(results) <= 3:
            return results

        reranked = [results[0]]
        remaining = results[1:]

        while remaining and len(reranked) < len(results):
            # Find the best item that's not too similar to the last few
            best = remaining[0]
            best_idx = 0

            for i, item in enumerate(remaining):
                # Check similarity to last 3 items
                max_sim = 0.0
                for prev in reranked[-3:]:
                    prev_emb = np.array(prev.entity.get("embedding", np.zeros(64)), dtype=np.float32)
                    item_emb = np.array(item.entity.get("embedding", np.zeros(64)), dtype=np.float32)
                    pn = np.linalg.norm(prev_emb) + 1e-10
                    in_n = np.linalg.norm(item_emb) + 1e-10
                    sim = float(np.dot(prev_emb / pn, item_emb / in_n))
                    max_sim = max(max_sim, sim)

                # Penalize high similarity
                adjusted = item.score - max(0, (max_sim - 0.7) * 0.3)
                if adjusted > best.score - max(0, (max_sim - 0.7) * 0.3):
                    best = item
                    best_idx = i

            reranked.append(best)
            remaining.pop(best_idx)

        return reranked
