#!/usr/bin/env python3
"""build_embeddings.py — offline pipeline: computes and stores all embeddings.

Produces: fighter embeddings, style vectors, stores in vector store.
Exports artifacts to artifacts/vectors/.
"""

import sys
import numpy as np

from intelligence.embeddings.fighter_embedder import embed_fighter, embed_fighter_batch
from intelligence.embeddings.style_vector import from_stats
from intelligence.vector_store.in_memory import InMemoryVectorStore
from intelligence.feature_store.serializer import save_vectors


def build_embeddings(fighters: list[dict]) -> tuple[np.ndarray, InMemoryVectorStore]:
    """Build all fighter embeddings. Returns (matrix, store)."""
    ids = [f.get("id", str(i)) for i, f in enumerate(fighters)]
    embeddings = np.zeros((len(fighters), 64), dtype=np.float32)
    store = InMemoryVectorStore()

    for i, f in enumerate(fighters):
        style = from_stats(
            slpm=f.get("slpm", 0), sa=f.get("striking_accuracy", 0),
            sd=f.get("striking_defense", 0), td=f.get("td_avg_per_15", 0),
            tda=f.get("td_accuracy", 0), tdd=f.get("td_defense", 0),
            sub=f.get("sub_avg_per_15", 0), fr=f.get("finish_rate", 0),
        )
        emb = embed_fighter(
            style, age=f.get("age", 30), h=f.get("height_cm", 178),
            r=f.get("reach_cm", 183), w=f.get("wins", 0), l=f.get("losses", 0),
            ko=f.get("ko_wins", 0), sub=f.get("sub_wins", 0),
            streak=f.get("streak", 0), rank=f.get("rank"),
            champ=f.get("champion", False),
        )
        embeddings[i] = emb
        store.add(f"fighter:{ids[i]}", emb)

    return embeddings, store


def export_embeddings(embeddings: np.ndarray, ids: list[str], path: str) -> None:
    save_vectors({"embeddings": embeddings, "ids": np.array(ids, dtype="S")}, path)


if __name__ == "__main__":
    print("Embedding pipeline — import and use programmatically")
