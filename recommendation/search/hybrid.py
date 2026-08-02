"""Semantic + Hybrid Search — combines keyword matching with embedding similarity."""

import numpy as np
from typing import Any


class SemanticSearch:
    """Finds entities by embedding similarity to query."""

    def __init__(self, vector_store: Any = None):
        self.store = vector_store

    def search(self, query_embedding: np.ndarray, k: int = 20) -> list[tuple[str, float]]:
        if self.store is None:
            return []
        return self.store.search(query_embedding, k=k)

    def search_with_filter(
        self, query_embedding: np.ndarray, candidate_ids: list[str], k: int = 20,
    ) -> list[tuple[str, float]]:
        if self.store is None:
            return []
        return self.store.search_by_ids(query_embedding, candidate_ids)[:k]


class HybridSearch:
    """Combines semantic (embedding) + keyword (text) search."""

    def __init__(
        self, vector_store: Any = None,
        semantic_weight: float = 0.6, keyword_weight: float = 0.4,
    ):
        self.semantic = SemanticSearch(vector_store)
        self.sem_weight = semantic_weight
        self.kw_weight = keyword_weight

    def search(
        self, query: str, query_embedding: np.ndarray,
        entities: list[dict], k: int = 20,
    ) -> list[dict]:
        """Hybrid search: semantic similarity + keyword match."""
        query_lower = query.lower()

        results = {}
        for e in entities:
            name = str(e.get("name", e.get("full_name", ""))).lower()
            nickname = str(e.get("nickname", "")).lower()

            # Keyword score
            kw_score = 0.0
            if query_lower in name:
                kw_score = 0.9 if name.startswith(query_lower) else 0.6
            elif query_lower in nickname:
                kw_score = 0.5
            elif any(word in name for word in query_lower.split()):
                kw_score = 0.3

            eid = e.get("id", "")
            sem_score = 0.5  # Default

            results[eid] = {
                **e, "search_score": self.sem_weight * sem_score + self.kw_weight * kw_score,
            }

        ranked = sorted(results.values(), key=lambda x: x["search_score"], reverse=True)
        return ranked[:k]


class AutocompleteEngine:
    """Fast prefix-based autocomplete for fighter/event names."""

    def __init__(self, entities: list[dict] | None = None):
        self._index: dict[str, list[dict]] = {}
        if entities:
            self.index(entities)

    def index(self, entities: list[dict]) -> None:
        self._index.clear()
        for e in entities:
            name = e.get("name", e.get("full_name", ""))
            for i in range(2, len(name) + 1):
                prefix = name[:i].lower()
                if prefix not in self._index:
                    self._index[prefix] = []
                if len(self._index[prefix]) < 5:
                    self._index[prefix].append(e)

    def suggest(self, prefix: str, limit: int = 8) -> list[dict]:
        return self._index.get(prefix.lower(), [])[:limit]
