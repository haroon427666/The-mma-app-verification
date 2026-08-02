"""Recommendation benchmarks — speed of every pipeline stage."""

import time
import numpy as np


def bench_pipeline(stages: dict[str, callable], iterations: int = 50) -> list[dict]:
    results = []
    for name, fn in stages.items():
        times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            fn()
            times.append((time.perf_counter() - t0) * 1000)
        times = np.array(times)
        results.append({
            "stage": name, "mean_ms": round(float(np.mean(times)), 3),
            "p95_ms": round(float(np.percentile(times, 95)), 3),
            "iterations": iterations,
        })
    return results


def bench_profiling():
    """Run the full pipeline benchmark."""
    from recommendation.user_profile.builder import UserProfileBuilder
    from recommendation.engine.recommendation_engine import RecommendationEngine

    builder = UserProfileBuilder()
    engine = RecommendationEngine()

    interactions = [
        {"type": "favorite_fighter", "weight": 1.0, "entity": {"fighter_id": "f1", "weight_class": "Lightweight", "style_vector": [0.5]*16}},
        {"type": "view_fighter", "weight": 0.8, "entity": {"fighter_id": "f2", "weight_class": "Lightweight", "style_vector": [0.6]*16}},
        {"type": "view_event", "weight": 0.5, "entity": {"promotion": "UFC", "weight_class": "Lightweight"}},
    ]

    fighters = [
        {"id": f"f{i}", "name": f"Fighter {i}", "type": "fighter", "weight_class": "Lightweight",
         "embedding": np.random.randn(64).astype(np.float32).tolist(),
         "finish_rate": 0.6, "elo_rating": 1500 + i * 20}
        for i in range(200)
    ]

    def build_profile():
        builder.build("test_user", interactions)

    def score_candidates():
        profile = builder.build("test_user", interactions)
        from recommendation.scoring.final_score import compute_final_score
        compute_final_score(profile, fighters[0], {}, set(), None, [])

    def full_recommendation():
        engine.recommend("test_user", interactions, fighters, k=20)

    return bench_pipeline({
        "profile_build": build_profile,
        "single_score": score_candidates,
        "full_recommend_200": full_recommendation,
    })
