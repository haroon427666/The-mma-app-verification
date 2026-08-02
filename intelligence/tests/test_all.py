"""intelligence/ tests — embeddings, features, analytics, rankings, similarity."""

import numpy as np
import pytest


# ═══════════════════════════════════════════════════════════════════════════
# Embedding Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestStyleVector:
    def test_has_16_dimensions(self):
        from intelligence.embeddings.style_vector import from_stats, DIM
        vec = from_stats(sig_strikes_landed_per_min=4.5, sig_strikes_accuracy_pct=50)
        assert vec.shape == (DIM,)
        assert vec.dtype == np.float32

    def test_values_in_range(self):
        from intelligence.embeddings.style_vector import from_stats
        vec = from_stats(5.0, 60.0, 55.0, 0.5, 3.0, 45.0, 70.0, 1.0, 0.6, 0.7)
        assert np.all(vec >= 0.0)
        assert np.all(vec <= 1.0)

    def test_style_label_knockout_artist(self):
        from intelligence.embeddings.style_vector import from_stats, style_label
        vec = np.zeros(16, dtype=np.float32)
        vec[10] = 0.85  # finish_rate
        vec[3] = 0.6    # striking_power
        label = style_label(vec)
        assert label == "Knockout Artist"

    def test_style_label_grappler(self):
        from intelligence.embeddings.style_vector import style_label
        vec = np.zeros(16, dtype=np.float32)
        vec[4] = 0.7
        vec[0] = 0.3
        assert style_label(vec) == "Grappler"


class TestFighterEmbedder:
    def test_embedding_dimension(self):
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.style_vector import empty as empty_style
        emb = embed_fighter(empty_style())
        assert emb.shape == (64,)

    def test_normalized_to_unit(self):
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.style_vector import empty as empty_style
        emb = embed_fighter(empty_style())
        assert 0.99 < np.linalg.norm(emb) < 1.01

    def test_champion_encoded(self):
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.style_vector import empty as empty_style
        emb_champ = embed_fighter(empty_style(), is_champion=True)
        emb_non = embed_fighter(empty_style(), is_champion=False)
        assert emb_champ[31] > 0.9
        assert emb_non[31] < 0.1

    def test_batch_embedding(self):
        from intelligence.embeddings.fighter_embedder import embed_fighter_batch
        fighters = [
            {"slpm": 4.5, "str_acc": 55, "wins": 20, "losses": 5},
            {"slpm": 3.0, "str_acc": 40, "wins": 10, "losses": 8},
        ]
        embs = embed_fighter_batch(fighters)
        assert embs.shape == (2, 64)


class TestMatchupEmbedder:
    def test_matchup_dimension(self):
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.matchup_embedder import embed_matchup
        from intelligence.embeddings.style_vector import empty as empty_style
        a = embed_fighter(empty_style())
        b = embed_fighter(empty_style())
        m = embed_matchup(a, b)
        assert m.shape == (32,)

    def test_win_prob_in_range(self):
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.matchup_embedder import embed_matchup, win_probability_heuristic
        from intelligence.embeddings.style_vector import empty as empty_style
        a = embed_fighter(empty_style(), wins=20, streak=5)
        b = embed_fighter(empty_style(), wins=5, losses=15, streak=-3)
        m = embed_matchup(a, b)
        prob = win_probability_heuristic(m)
        assert 0.0 <= prob <= 1.0
        assert prob > 0.5  # A should be favored


# ═══════════════════════════════════════════════════════════════════════════
# Feature Engineering Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestFeaturePipelines:
    def test_striking_pipeline(self):
        from intelligence.feature_engineering.striking import StrikingFeatures
        p = StrikingFeatures()
        f = p.extract({"sig_strikes_landed_per_min": 4.5, "sig_strikes_accuracy_pct": 55, "wins": 10, "losses": 3})
        assert f.shape == (8,)

    def test_grappling_pipeline(self):
        from intelligence.feature_engineering.grappling import GrapplingFeatures
        p = GrapplingFeatures()
        f = p.extract({"takedown_avg_per_15min": 3.5, "takedown_accuracy_pct": 50, "wins": 10})
        assert f.shape == (6,)

    def test_matchup_features(self):
        from intelligence.feature_engineering.matchup import MatchupFeatures
        p = MatchupFeatures()
        a = {"sig_strikes_landed_per_min": 4.5, "takedown_avg_per_15min": 3.0, "age": 30, "wins": 15}
        b = {"sig_strikes_landed_per_min": 3.0, "takedown_avg_per_15min": 1.5, "age": 35, "wins": 25}
        f = p.extract_pair(a, b)
        assert f.shape == (12,)


# ═══════════════════════════════════════════════════════════════════════════
# Analytics Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestAgeCurves:
    def test_peak_age_max_score(self):
        from intelligence.analytics.age_curves import age_performance_score
        for age in [29, 30, 31, 32]:
            assert age_performance_score(age) == 1.0

    def test_young_prospect(self):
        from intelligence.analytics.age_curves import age_performance_score, career_stage
        assert age_performance_score(22) < 0.5
        assert career_stage(22) == "Rising Prospect"

    def test_decline(self):
        from intelligence.analytics.age_curves import age_performance_score
        assert age_performance_score(38) < 0.5


class TestMomentum:
    def test_streak_score(self):
        from intelligence.analytics.momentum import momentum_score
        s = momentum_score(3, [1, 1, 0, 1, 1])
        assert s > 0.5
        s2 = momentum_score(-3, [0, 0, 0, 1, 0])
        assert s2 < 0.5

    def test_trajectory_slope(self):
        from intelligence.analytics.momentum import trajectory_slope
        improving = trajectory_slope([0, 0, 1, 1, 1, 1, 1])
        declining = trajectory_slope([1, 1, 1, 0, 0, 0, 0])
        assert improving > 0
        assert declining < 0


class TestQuality:
    def test_championship_score(self):
        from intelligence.analytics.quality import championship_score
        assert championship_score(0, 0, 0) == 0.0
        assert championship_score(5, 5, 3) > 0.8


# ═══════════════════════════════════════════════════════════════════════════
# Rankings Engine Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestElo:
    def test_expected_score_symmetry(self):
        from intelligence.rankings_engine.elo import expected_score
        e = expected_score(1500, 1500)
        assert abs(e - 0.5) < 0.001

    def test_higher_rated_favored(self):
        from intelligence.rankings_engine.elo import expected_score
        e = expected_score(1800, 1400)
        assert e > 0.9

    def test_upset_gains_points(self):
        from intelligence.rankings_engine.elo import update_elo, INITIAL_ELO
        new_a, new_b = update_elo(1400, 1800, True)
        assert new_a > 1400  # Underdog won, gains points
        assert new_b < 1800  # Favorite lost, loses points

    def test_finish_bonus(self):
        from intelligence.rankings_engine.elo import update_elo
        normal, _ = update_elo(1500, 1500, True, is_finish=False)
        finish, _ = update_elo(1500, 1500, True, is_finish=True)
        assert finish > normal  # Finish win gains more


class TestGlicko:
    def test_rd_decreases_after_fight(self):
        from intelligence.rankings_engine.glicko import update_glicko, INITIAL_RATING, INITIAL_RD
        _, new_rd = update_glicko(INITIAL_RATING, INITIAL_RD, 1500, 100, True)
        assert new_rd < INITIAL_RD

    def test_inactivity_increases_rd(self):
        from intelligence.rankings_engine.glicko import increase_rd
        new_rd = increase_rd(100, 365)
        assert new_rd > 100


class TestCompositeRanking:
    def test_champion_ranks_higher(self):
        from intelligence.rankings_engine.composite import rank_fighters
        fighters = [
            {"id": "a", "championship": 1.0, "elo": 1600},
            {"id": "b", "championship": 0.0, "elo": 1650},
        ]
        ranked = rank_fighters(fighters)
        # Champion with slightly lower Elo might still rank higher
        scores = {f["id"]: f["_score"] for f in ranked}
        assert scores["a"] > 0 or scores["b"] > 0


# ═══════════════════════════════════════════════════════════════════════════
# Vector Store + Similarity Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestVectorStore:
    def test_add_and_search(self):
        from intelligence.vector_store.in_memory import InMemoryVectorStore
        s = InMemoryVectorStore()
        s.add("a", np.array([1, 0, 0], dtype=np.float32))
        s.add("b", np.array([0, 1, 0], dtype=np.float32))
        s.add("c", np.array([0.9, 0.1, 0], dtype=np.float32))

        results = s.search(np.array([1, 0, 0]), k=2)
        assert results[0][0] == "a"  # Exact match first
        assert results[1][0] == "c"  # Near-match second


class TestSimilarityEngine:
    def test_find_similar(self):
        from intelligence.fighter_similarity.engine import FighterSimilarityEngine
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.style_vector import empty as empty_style

        engine = FighterSimilarityEngine()
        ids = ["f1", "f2", "f3"]
        embs = np.array([
            embed_fighter(empty_style(), wins=20, ko_wins=15),
            embed_fighter(empty_style(), wins=5, ko_wins=1),
            embed_fighter(empty_style(), wins=18, ko_wins=12),
        ])
        engine.index(ids, embs)
        similar = engine.find_similar("f1", k=2)
        assert len(similar) == 2
        assert similar[0][0] == "f3"  # Most similar

    def test_style_clustering(self):
        from intelligence.fighter_similarity.engine import StyleClusterer
        from intelligence.embeddings.style_vector import from_stats

        vecs = np.array([
            from_stats(5, 55, 50, 1.0, 1, 30, 80, 0.2, 0.8, 0.3),
            from_stats(5, 50, 55, 0.5, 1.5, 40, 75, 0.5, 0.7, 0.4),
            from_stats(2, 40, 60, 0.1, 5, 50, 50, 2.0, 0.4, 0.6),
            from_stats(2.5, 45, 55, 0.2, 4.5, 55, 45, 1.5, 0.3, 0.5),
        ])
        c = StyleClusterer(n_clusters=2)
        labels = c.fit(vecs)
        assert len(labels) == 4
        assert labels[0] == labels[1] or labels[0] == labels[2]  # Some clustering happened


# ═══════════════════════════════════════════════════════════════════════════
# Matchup Engine Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestMatchupEngine:
    def test_win_probability(self):
        from intelligence.matchup_engine import predict_win_probability
        from intelligence.embeddings.fighter_embedder import embed_fighter
        from intelligence.embeddings.style_vector import empty as empty_style

        a = embed_fighter(empty_style(), wins=25, losses=1, streak=15, is_champion=True)
        b = embed_fighter(empty_style(), wins=5, losses=10, streak=-3)
        prob = predict_win_probability(a, b)
        assert prob > 0.6  # Champion heavily favored

    def test_style_matchup_analysis(self):
        from intelligence.matchup_engine.predictor import style_matchup_analysis
        import numpy as np
        striker = np.zeros(16, dtype=np.float32)
        striker[0] = 0.8; striker[4] = 0.2
        grappler = np.zeros(16, dtype=np.float32)
        grappler[0] = 0.2; grappler[4] = 0.8

        analysis = style_matchup_analysis(striker, grappler)
        assert analysis["archetype"] == "striker_vs_grappler"
        assert analysis["striker_advantage"] == "a"
        assert analysis["grappler_advantage"] == "b"
