"""Vector Store — in-memory exact + approximate nearest neighbor search.

Stores fighter/matchup embeddings and provides similarity search.
"""

import numpy as np
from typing import Optional


class InMemoryVectorStore:
    """Stores embeddings and enables fast cosine-similarity search.

    Usage:
        store = InMemoryVectorStore()
        store.add("fighter:abc123", embedding)
        similar = store.search(query_vec, k=10)
    """

    def __init__(self):
        self._ids: list[str] = []
        self._vectors: list[np.ndarray] = []

    def add(self, item_id: str, vector: np.ndarray) -> None:
        self._ids.append(item_id)
        self._vectors.append(vector.astype(np.float32))

    def add_batch(self, ids: list[str], vectors: np.ndarray) -> None:
        for i, vid in enumerate(ids):
            self._ids.append(vid)
            self._vectors.append(vectors[i].astype(np.float32))

    def remove(self, item_id: str) -> bool:
        for i, vid in enumerate(self._ids):
            if vid == item_id:
                del self._ids[i]
                del self._vectors[i]
                return True
        return False

    @property
    def size(self) -> int:
        return len(self._ids)

    def get_vector(self, item_id: str) -> Optional[np.ndarray]:
        for i, vid in enumerate(self._ids):
            if vid == item_id:
                return self._vectors[i].copy()
        return None

    def search(self, query: np.ndarray, k: int = 10) -> list[tuple[str, float]]:
        """Return top-k similar items by cosine similarity."""
        if self.size == 0:
            return []

        query = query.astype(np.float32)
        q_norm = query / (np.linalg.norm(query) + 1e-10)

        results = []
        for i, vec in enumerate(self._vectors):
            v_norm = vec / (np.linalg.norm(vec) + 1e-10)
            sim = float(np.dot(q_norm, v_norm))
            results.append((self._ids[i], sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def search_by_ids(
        self, query: np.ndarray, candidate_ids: list[str],
    ) -> list[tuple[str, float]]:
        """Search only within specific IDs."""
        query = query.astype(np.float32)
        q_norm = query / (np.linalg.norm(query) + 1e-10)
        results = []

        for i, vid in enumerate(self._ids):
            if vid in candidate_ids:
                v_norm = self._vectors[i] / (np.linalg.norm(self._vectors[i]) + 1e-10)
                sim = float(np.dot(q_norm, v_norm))
                results.append((vid, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def to_matrix(self) -> np.ndarray:
        return np.array(self._vectors, dtype=np.float32)
