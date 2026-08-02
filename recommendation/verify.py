#!/usr/bin/env python3
"""Verify the recommendation/ package — all modules tested."""

import sys
import numpy as np


def run():
    print("=" * 60)
    print("RECOMMENDATION PACKAGE VERIFICATION")
    print("=" * 60)
    p = 0

    # ── 1. User Profile Builder ──────────────────────────────────────
    print("\n1. USER PROFILE")
    from recommendation.user_profile.builder import UserProfileBuilder, UserProfile

    builder = UserProfileBuilder()
    interactions = [
        {"type": "favorite_fighter", "weight": 1.0,
         "entity": {"fighter_id": "f1", "weight_class": "Lightweight", "style_vector": [0.5]*16}},
        {"type": "view_fighter", "weight": 0.8,
         "entity": {"fighter_id": "f2", "weight_class": "Lightweight", "style_vector": [0.6]*16}},
        {"type": "view_event", "weight": 0.5,
         "entity": {"weight_class": "Lightweight", "promotion": "UFC"}},
        {"type": "favorite_fighter", "weight": 1.0,
         "entity": {"fighter_id": "f3", "weight_class": "Welterweight", "style_vector": [0.3]*16}},
    ]
    profile = builder.build("user1", interactions)
    assert profile.user_id == "user1"
    assert profile._total_interactions == 4
    assert profile.top_weight_classes[0] == "Lightweight"
    assert len(profile.top_fighters) == 3
    print(f"  ✓ Profile: {profile._total_interactions} interactions, top wc: {profile.top_weight_classes[0]}")
    p += 1

    # ── 2. Scoring Signals ──────────────────────────────────────────
    print("\n2. SCORING")
    from recommendation.scoring.final_score import (
        personalization_score, freshness_score, quality_score,
        compute_final_score, diversity_penalty, novelty_bonus,
    )

    entity = {"id": "f1", "weight_class": "Lightweight", "finish_rate": 0.7,
              "elo_rating": 1800, "is_title_fight": False, "embedding": np.random.randn(64).tolist()}

    ps = personalization_score(profile, entity, 0.30)
    fs = freshness_score(entity, 0.12)
    qs = quality_score(entity, 0.10)
    assert 0 <= ps.score <= 1 and 0 <= fs.score <= 1 and 0 <= qs.score <= 1
    print(f"  ✓ personalization={ps.score:.2f} freshness={fs.score:.2f} quality={qs.score:.2f}")

    final, reasons = compute_final_score(profile, entity, {}, set(), None, [])
    assert 0 <= final <= 1
    print(f"  ✓ Final score: {final:.3f}, reasons: {reasons}")
    p += 1

    # ── 3. Recommendation Engine ────────────────────────────────────
    print("\n3. RECOMMENDATION ENGINE")
    from recommendation.engine.recommendation_engine import RecommendationEngine

    engine = RecommendationEngine()
    fighters = [
        {"id": f"f{i}", "name": f"Fighter {i}", "type": "fighter", "weight_class": "Lightweight",
         "finish_rate": 0.5 + i * 0.02, "elo_rating": 1500 + i * 30,
         "embedding": (np.random.randn(64) * 0.1 + (np.array([0.5]*16 + [0]*48))).tolist()}
        for i in range(50)
    ]
    results = engine.recommend("user1", interactions, fighters, k=10)
    assert len(results) == 10
    assert all(hasattr(r, "score") and hasattr(r, "reasons") for r in results)
    print(f"  ✓ {len(results)} recommendations, top: {results[0].to_dict()['name']} ({results[0].score:.3f})")
    p += 1

    # ── 4. Retrieval ────────────────────────────────────────────────
    print("\n4. RETRIEVAL")
    from recommendation.retrieval.candidates import FighterRetrieval, EventRetrieval

    fr = FighterRetrieval()
    candidates = fr.get_candidates(fighters, 20)
    assert len(candidates) == 20
    assert all(c["type"] == "fighter" for c in candidates)

    er = EventRetrieval()
    events = [{"id": "e1", "name": "UFC 400", "status": "SCHEDULED", "fight_count": 13}]
    ev = er.get_upcoming(events)
    assert len(ev) == 1
    print(f"  ✓ Fighters: {len(candidates)}, Events upcoming: {len(ev)}")
    p += 1

    # ── 5. Explainability ───────────────────────────────────────────
    print("\n5. EXPLAINABILITY")
    from recommendation.explainability.reasons import explain_recommendation, generate_contextual_reasons

    rec = results[0].to_dict()
    exp = explain_recommendation(rec)
    assert "reasons" in exp and "confidence" in exp
    ctx = generate_contextual_reasons({"is_champion": True, "streak": 5, "finish_rate": 0.8}, {})
    assert len(ctx) >= 2
    print(f"  ✓ Explained: confidence={exp['confidence']}, contextual reasons: {len(ctx)}")
    p += 1

    # ── 6. Trending ─────────────────────────────────────────────────
    print("\n6. TRENDING")
    from recommendation.trending.fighters import TrendingEngine

    te = TrendingEngine(window_days=7, min_views=2)
    for _ in range(20):
        te.record_view("f1")
        te.record_view("f2")
    for _ in range(5):
        te.record_view("f3")

    v1 = te.velocity("f1")
    v3 = te.velocity("f3")
    assert v1 > v3
    top = te.top_trending(["f1", "f2", "f3", "f4"], k=3)
    assert len(top) >= 2
    print(f"  ✓ f1 velocity={v1:.1f}/h, f3={v3:.1f}/h, trending: {len(top)} entities")
    p += 1

    # ── 7. Search ───────────────────────────────────────────────────
    print("\n7. SEARCH")
    from recommendation.search.hybrid import AutocompleteEngine, HybridSearch

    ac = AutocompleteEngine()
    ac.index([{"id": "f1", "name": "Islam Makhachev"}, {"id": "f2", "name": "Israel Adesanya"}])
    sug = ac.suggest("isl")
    assert len(sug) == 1 and sug[0]["name"] == "Islam Makhachev"

    hs = HybridSearch()
    results_s = hs.search("islam", np.random.randn(64).astype(np.float32),
                          [{"id": "f1", "name": "Islam Makhachev", "nickname": ""},
                           {"id": "f2", "name": "Israel Adesanya", "nickname": ""}])
    assert results_s[0]["id"] == "f1"
    print(f"  ✓ Autocomplete 'isl'→Islam, search 'islam' top: {results_s[0]['name']}")
    p += 1

    # ── 8. A/B Testing ─────────────────────────────────────────────
    print("\n8. A/B TESTING")
    from recommendation.experiments.ab_testing import Experiment, ExperimentTracker

    exp = Experiment("scoring_v2", ["control", "variant_a"], [0.5, 0.5])
    tracker = ExperimentTracker()
    tracker.register(exp)
    v = tracker.get_variant("scoring_v2", "user_abc")
    assert v in ("control", "variant_a")
    # Same user always gets same variant
    assert tracker.get_variant("scoring_v2", "user_abc") == v
    print(f"  ✓ Experiment: user_abc → {v}, deterministic")
    p += 1

    # ── 9. Evaluation ───────────────────────────────────────────────
    print("\n9. EVALUATION")
    from recommendation.evaluation.metrics import precision_at_k, ndcg_at_k, diversity_score

    recs = ["f1", "f2", "f3", "f4", "f5"]
    relevant = {"f1", "f3", "f5"}
    p_at_5 = precision_at_k(recs, relevant, 5)
    assert p_at_5 == 0.6

    nd = ndcg_at_k(recs, {"f1": 3, "f2": 0, "f3": 2, "f4": 0, "f5": 1}, 5)
    assert nd > 0

    div = diversity_score([{"embedding": [1,0,0]}, {"embedding": [0,1,0]}, {"embedding": [0,0,1]}])
    assert div > 0.9  # Very diverse
    print(f"  ✓ P@5={p_at_5:.2f}, NDCG@5={nd:.3f}, diversity={div:.3f}")
    p += 1

    # ── 10. Notifications ──────────────────────────────────────────
    print("\n10. NOTIFICATIONS")
    from recommendation.notifications import WatchlistChecker, DigestBuilder

    wc = WatchlistChecker()
    triggers = wc.check_event_starting({"id": "e1", "name": "UFC 400"}, ["user1", "user2"])
    assert len(triggers) == 2
    assert triggers[0].type == "event_starting"

    db = DigestBuilder()
    digest = db.build("user1", [{"id": "f1", "name": "Makhachev vs Oliveira"}],
                      [{"id": "f2", "name": "Shavkat Rakhmonov"}])
    assert digest.type == "weekly_digest"
    print(f"  ✓ {len(triggers)} event triggers + weekly digest: {digest.title}")
    p += 1

    print(f"\n{'='*60}")
    print(f"RECOMMENDATION: {p}/10 sections VERIFIED")
    print(f"{'='*60}")
    return p == 10


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
