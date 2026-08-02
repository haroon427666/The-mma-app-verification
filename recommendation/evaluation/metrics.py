"""Recommendation Evaluation — Precision@K, Recall@K, MAP, NDCG, diversity, coverage."""

import math
import numpy as np
from typing import Any


def precision_at_k(recommended: list[str], relevant: set[str], k: int = 20) -> float:
    if k <= 0: return 0.0
    hits = sum(1 for r in recommended[:k] if r in relevant)
    return hits / k


def recall_at_k(recommended: list[str], relevant: set[str], k: int = 20) -> float:
    if not relevant: return 0.0
    hits = sum(1 for r in recommended[:k] if r in relevant)
    return hits / len(relevant)


def average_precision(recommended: list[str], relevant: set[str]) -> float:
    if not relevant: return 0.0
    hits = 0
    total = 0.0
    for i, r in enumerate(recommended):
        if r in relevant:
            hits += 1
            total += hits / (i + 1)
    return total / len(relevant)


def mean_average_precision(all_recommended: list[list[str]], all_relevant: list[set[str]]) -> float:
    if not all_recommended: return 0.0
    return sum(average_precision(r, rel) for r, rel in zip(all_recommended, all_relevant)) / len(all_recommended)


def ndcg_at_k(recommended: list[str], relevant: dict[str, float], k: int = 20) -> float:
    dcg = 0.0
    for i, r in enumerate(recommended[:k]):
        rel = relevant.get(r, 0)
        dcg += rel / math.log2(i + 2)
    ideal = sorted(relevant.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def diversity_score(recommended: list[dict], embedding_key: str = "embedding") -> float:
    if len(recommended) < 2: return 1.0
    embeddings = [np.array(r.get(embedding_key, np.zeros(64)), dtype=np.float32) for r in recommended]
    sims = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            a, b = embeddings[i], embeddings[j]
            an, bn = np.linalg.norm(a) + 1e-10, np.linalg.norm(b) + 1e-10
            sims.append(float(np.dot(a / an, b / bn)))
    return 1.0 - np.mean(sims)


def coverage(all_recommended: list[list[str]], catalog_ids: set[str]) -> float:
    recommended_ids = set()
    for recs in all_recommended:
        recommended_ids.update(recs)
    return len(recommended_ids) / len(catalog_ids) if catalog_ids else 0.0


def novelty_score(recommended: list[str], popularity: dict[str, int], k: int = 20) -> float:
    max_pop = max(popularity.values()) if popularity else 1
    if max_pop == 0: return 1.0
    novelties = [1.0 - popularity.get(r, 0) / max_pop for r in recommended[:k]]
    return sum(novelties) / len(novelties) if novelties else 0.0
