#!/usr/bin/env python3
"""Verify the intelligence/ package — all modules tested."""

import sys
import numpy as np

def run():
    print("=" * 60)
    print("INTELLIGENCE PACKAGE VERIFICATION")
    print("=" * 60)
    passed = 0

    # ── 1. Embeddings ─────────────────────────────────────────────────
    print("\n1. EMBEDDINGS")
    from intelligence.embeddings.style_vector import from_stats, style_label, empty as empty_style, DIM
    from intelligence.embeddings.fighter_embedder import embed_fighter, embed_fighter_batch
    from intelligence.embeddings.matchup_embedder import embed_matchup, win_probability_heuristic

    style = from_stats(5.0, 55, 60, 0.5, 3.0, 45, 70, 1.0, 0.7, 0.6)
    assert style.shape == (16,), f"Style vector: {style.shape}"
    assert np.all(style >= 0) and np.all(style <= 1)

    emb = embed_fighter(style, wins=20, losses=5, streak=5, is_champion=True)
    assert emb.shape == (64,)
    assert 0.999 < np.linalg.norm(emb) < 1.001, f"Norm: {np.linalg.norm(emb)}"

    emb2 = embed_fighter(empty_style())
    m = embed_matchup(emb, emb2)
    assert m.shape == (32,)
    prob = win_probability_heuristic(m)
    assert 0 <= prob <= 1
    print(f"  ✓ Style vector: {DIM}d, fighter: 64d, matchup: 32d, win prob: {prob:.3f}")
    passed += 1

    # ── 2. Feature Engineering ────────────────────────────────────────
    print("\n2. FEATURE ENGINEERING")
    from intelligence.feature_engineering.striking import StrikingFeatures
    from intelligence.feature_engineering.grappling import GrapplingFeatures
    from intelligence.feature_engineering.physical import PhysicalFeatures
    from intelligence.feature_engineering.momentum import MomentumFeatures
    from intelligence.feature_engineering.career import CareerFeatures
    from intelligence.feature_engineering.matchup import MatchupFeatures

    f = {"sig_strikes_landed_per_min": 4.5, "sig_strikes_accuracy_pct": 55, "wins": 10, "losses": 3,
         "takedown_avg_per_15min": 3.0, "takedown_accuracy_pct": 50, "age": 30, "height_cm": 178,
         "reach_cm": 183, "streak": 3, "ko_wins": 5, "sub_wins": 2, "title_wins": 1}

    dims = [
        ("striking", StrikingFeatures(), 8),
        ("grappling", GrapplingFeatures(), 6),
        ("physical", PhysicalFeatures(), 6),
        ("momentum", MomentumFeatures(), 4),
        ("career", CareerFeatures(), 4),
    ]
    for name, pipe, expected in dims:
        result = pipe.extract(f)
        assert result.shape == (expected,), f"{name}: expected {expected}d, got {result.shape}"
    mf = MatchupFeatures()
    mp = mf.extract_pair(f, {**f, "age": 35, "wins": 25, "losses": 8})
    assert mp.shape == (12,)
    print(f"  ✓ 6 pipelines: striking(8) grappling(6) physical(6) momentum(4) career(4) matchup(12)")
    passed += 1

    # ── 3. Analytics ──────────────────────────────────────────────────
    print("\n3. ANALYTICS")
    from intelligence.analytics.age_curves import age_performance_score, career_stage
    from intelligence.analytics.momentum import momentum_score, trajectory_slope
    from intelligence.analytics.pace import activity_rate, pressure_score
    from intelligence.analytics.quality import opponent_quality_score, championship_score
    from intelligence.analytics.trajectory import trajectory_score

    assert age_performance_score(30) == 1.0
    assert age_performance_score(22) < 0.5
    assert career_stage(30) == "Prime"
    assert career_stage(22) == "Rising Prospect"

    ms = momentum_score(4, [1, 1, 1, 0, 1])
    assert ms > 0.6
    improving = trajectory_slope([0, 0, 1, 1, 1, 1, 1])
    declining = trajectory_slope([1, 1, 1, 0, 0, 0, 0])
    assert improving > declining

    ar = activity_rate(20, 6)
    assert 0.5 < ar < 1.5
    ps = pressure_score(4.5, 3.0, 2.0)
    assert 0 < ps < 1
    assert championship_score(3, 2, 1) > 0.4
    assert championship_score(0, 0, 0) == 0.0
    print(f"  ✓ Age curve peak=30, career stages, momentum, pace, quality all correct")
    passed += 1

    # ── 4. Rankings ───────────────────────────────────────────────────
    print("\n4. RANKINGS ENGINE")
    from intelligence.rankings_engine.elo import update_elo, expected_score, INITIAL_ELO
    from intelligence.rankings_engine.glicko import update_glicko, INITIAL_RATING, INITIAL_RD
    from intelligence.rankings_engine.composite import composite_ranking_score, rank_fighters

    assert abs(expected_score(1500, 1500) - 0.5) < 0.01
    assert expected_score(1800, 1400) > 0.9
    a_new, b_new = update_elo(1400, 1800, True)
    assert a_new > 1400 and b_new < 1800  # Upset gains for underdog

    _, rd = update_glicko(INITIAL_RATING, INITIAL_RD, 1500, 100, True)
    assert rd < INITIAL_RD  # RD decreases with fights

    cs = composite_ranking_score(elo_rating=1800, championship=1.0, momentum=0.9, finish_rate=0.8)
    assert cs > 700
    ranked = rank_fighters([
        {"id": "a", "elo": 1600}, {"id": "b", "elo": 1800}, {"id": "c", "elo": 1400},
    ])
    assert ranked[0]["id"] == "b"  # Highest Elo first
    print(f"  ✓ Elo upset correct, Glicko RD decreases, composite ranks correctly")
    passed += 1

    # ── 5. Vector Store + Similarity ─────────────────────────────────
    print("\n5. VECTOR STORE + SIMILARITY")
    from intelligence.vector_store.in_memory import InMemoryVectorStore
    s = InMemoryVectorStore()
    s.add("a", np.array([1, 0, 0], dtype=np.float32))
    s.add("b", np.array([0, 1, 0], dtype=np.float32))
    s.add("c", np.array([0.9, 0.1, 0], dtype=np.float32))
    results = s.search(np.array([1, 0, 0]), k=2)
    assert results[0][0] == "a"
    assert results[1][0] == "c"
    assert s.size == 3

    from intelligence.fighter_similarity.engine import FighterSimilarityEngine, StyleClusterer
    engine = FighterSimilarityEngine()
    from intelligence.embeddings.fighter_embedder import embed_fighter
    from intelligence.embeddings.style_vector import empty as empty_style
    ids = ["f1", "f2", "f3"]
    embs = np.array([
        embed_fighter(empty_style(), wins=20, ko_wins=15),
        embed_fighter(empty_style(), wins=5, ko_wins=1),
        embed_fighter(empty_style(), wins=18, ko_wins=12),
    ])
    engine.index(ids, embs)
    similar = engine.find_similar("f1", k=2)
    assert len(similar) == 2

    clusterer = StyleClusterer(n_clusters=2)
    vecs = np.array([from_stats(5, 55, 50, 1, 1, 30, 80, 0.2, 0.8, 0.3),
                     from_stats(2, 40, 60, 0.1, 5, 50, 50, 2, 0.4, 0.6)])
    labels = clusterer.fit(vecs)
    assert len(labels) == 2
    print(f"  ✓ Vector store: 3 items, search correct, similarity engine + clustering work")
    passed += 1

    # ── 6. Matchup Engine ────────────────────────────────────────────
    print("\n6. MATCHUP ENGINE")
    from intelligence.matchup_engine import predict_win_probability, style_matchup_analysis
    a = embed_fighter(empty_style(), wins=25, streak=15, is_champion=True)
    b = embed_fighter(empty_style(), wins=5, streak=-3)
    prob = predict_win_probability(a, b)
    assert prob > 0.6

    striker = np.zeros(16, dtype=np.float32); striker[0] = 0.8; striker[4] = 0.2
    grappler = np.zeros(16, dtype=np.float32); grappler[0] = 0.2; grappler[4] = 0.8
    analysis = style_matchup_analysis(striker, grappler)
    assert analysis["archetype"] == "striker_vs_grappler"
    print(f"  ✓ Win prob: {prob:.3f}, archetype: {analysis['archetype']}")
    passed += 1

    print(f"\n{'='*60}")
    print(f"INTELLIGENCE PACKAGE: {passed}/6 sections VERIFIED")
    print(f"{'='*60}")
    return passed == 6

if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
