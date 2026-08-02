"""Benchmarks — measure speed of every intelligence operation.

Know exactly how fast each pipeline runs.
"""

import time
import numpy as np


def benchmark(fn, name: str = "", iterations: int = 100) -> dict:
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)

    times = np.array(times)
    return {
        "name": name,
        "mean_ms": round(float(np.mean(times)), 3),
        "p50_ms": round(float(np.percentile(times, 50)), 3),
        "p95_ms": round(float(np.percentile(times, 95)), 3),
        "p99_ms": round(float(np.percentile(times, 99)), 3),
        "min_ms": round(float(np.min(times)), 3),
        "max_ms": round(float(np.max(times)), 3),
        "iterations": iterations,
    }


def bench_embedding(fighters: list[dict]) -> dict:
    from intelligence.pipeline.build_embeddings import build_embeddings
    return benchmark(lambda: build_embeddings(fighters), "embedding_build", min(len(fighters), 10))


def bench_similarity(store, queries: int = 100) -> dict:
    from intelligence.vector_store.in_memory import InMemoryVectorStore
    vec = store.to_matrix()
    q = vec[0] if len(vec) > 0 else np.random.randn(64).astype(np.float32)

    def run():
        store.search(q, k=10)
    return benchmark(run, "similarity_search", queries)


def bench_rankings(fighters_or_fights, iterations: int = 50) -> dict:
    from intelligence.pipeline.rebuild_rankings import rebuild_rankings
    def run():
        rebuild_rankings(fighters_or_fights.get("fights", []),
                        fighters_or_fights.get("lookup", {}))
    return benchmark(run, "ranking_rebuild", min(iterations, 10))


def bench_prediction(emb_a: np.ndarray, emb_b: np.ndarray, iterations: int = 1000) -> dict:
    from intelligence.matchup_engine.predictor import predict_win_probability
    def run():
        predict_win_probability(emb_a, emb_b)
    return benchmark(run, "win_prediction", iterations)


def run_all(fighters: list[dict] | None = None, fights_data: dict | None = None) -> list[dict]:
    results = []

    if fighters:
        embs, store = __import__("intelligence.pipeline.build_embeddings",
                                 fromlist=[""]).build_embeddings(fighters)
        results.append(bench_embedding(fighters))
        results.append(bench_similarity(store))
        if embs is not None and len(embs) >= 2:
            results.append(bench_prediction(embs[0], embs[1]))

    if fights_data:
        results.append(bench_rankings(fights_data))

    return results
