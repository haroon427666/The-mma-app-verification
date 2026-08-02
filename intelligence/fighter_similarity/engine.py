"""Fighter Similarity Engine — finds similar fighters by embedding distance.

Uses cosine similarity over the 64-dim fighter embedding.
"""

import numpy as np
from typing import Optional

from intelligence.vector_store.in_memory import InMemoryVectorStore


class FighterSimilarityEngine:
    """Finds similar fighters using embedding cosine similarity."""

    def __init__(self, store: Optional[InMemoryVectorStore] = None):
        self.store = store or InMemoryVectorStore()

    def index(self, fighter_ids: list[str], embeddings: np.ndarray) -> None:
        self.store.add_batch(fighter_ids, embeddings)

    def find_similar(
        self, fighter_id: str, k: int = 10,
    ) -> list[tuple[str, float]]:
        """Find k most similar fighters by cosine similarity.

        Returns list of (fighter_id, similarity_score) sorted by similarity.
        """
        vec = self.store.get_vector(fighter_id)
        if vec is None:
            return []
        return self.store.search(vec, k=k + 1)[1:]  # Skip self

    def find_similar_to_vector(
        self, vector: np.ndarray, k: int = 10,
    ) -> list[tuple[str, float]]:
        return self.store.search(vector, k=k)

    def find_similar_in_division(
        self, fighter_id: str, division_ids: list[str], k: int = 10,
    ) -> list[tuple[str, float]]:
        """Find similar fighters within a specific division."""
        vec = self.store.get_vector(fighter_id)
        if vec is None:
            return []
        return self.store.search_by_ids(vec, division_ids)[:k + 1][1:]


class StyleClusterer:
    """Simple K-Means clustering on 16-dim style vectors."""

    def __init__(self, n_clusters: int = 8):
        self.n_clusters = n_clusters
        self.centroids_: Optional[np.ndarray] = None
        self.labels_: Optional[np.ndarray] = None

    def fit(self, style_vectors: np.ndarray, max_iter: int = 100) -> np.ndarray:
        """Cluster style vectors. Returns labels."""
        n = style_vectors.shape[0]
        rng = np.random.default_rng(42)

        # Initialize centroids by random points + k-means++
        self.centroids_ = style_vectors[rng.choice(n, self.n_clusters, replace=False)].copy()

        for _ in range(max_iter):
            # Assign
            labels = np.argmin(
                np.linalg.norm(style_vectors[:, None] - self.centroids_[None], axis=2),
                axis=1,
            )
            # Update centroids
            new_centroids = np.array([
                style_vectors[labels == k].mean(axis=0) if (labels == k).sum() > 0
                else style_vectors[rng.integers(n)]
                for k in range(self.n_clusters)
            ])
            if np.allclose(self.centroids_, new_centroids):
                break
            self.centroids_ = new_centroids

        self.labels_ = labels
        return labels

    def predict(self, style_vectors: np.ndarray) -> np.ndarray:
        return np.argmin(
            np.linalg.norm(style_vectors[:, None] - self.centroids_[None], axis=2),
            axis=1,
        )
