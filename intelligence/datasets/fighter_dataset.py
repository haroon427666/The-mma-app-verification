"""Datasets — transform fighters/fights into structured ML-ready data.

ML doesn't consume fighters. ML consumes datasets.
These builders produce flat feature-label tables.
"""

import numpy as np
from typing import Optional

from intelligence.feature_store.registry import feature_names
from intelligence.feature_store.repository import FeatureRepository
from intelligence.embeddings.fighter_embedder import embed_fighter
from intelligence.embeddings.style_vector import from_stats


class FighterDatasetBuilder:
    """Builds (N, F) feature matrix from fighter data."""

    def __init__(self, repo: Optional[FeatureRepository] = None):
        self.repo = repo or FeatureRepository()

    def build(self, fighters: list[dict], feature_list: list[str] | None = None) -> np.ndarray:
        """Convert fighter dicts to feature matrix."""
        if feature_list is None:
            feature_list = feature_names("physical") + feature_names("striking") + \
                feature_names("grappling") + feature_names("record") + feature_names("momentum")

        n = len(fighters)
        d = len(feature_list)
        matrix = np.zeros((n, d), dtype=np.float32)

        for i, f in enumerate(fighters):
            for j, fname in enumerate(feature_list):
                matrix[i, j] = f.get(fname, 0.0)

        return matrix

    def build_with_embeddings(self, fighters: list[dict]) -> np.ndarray:
        """Build feature matrix with fighter embeddings concatenated."""
        features = self.build(fighters)
        styles = np.array([from_stats(
            slpm=f.get("slpm", 0), sa=f.get("striking_accuracy", 0),
            sd=f.get("striking_defense", 0), td=f.get("td_avg_per_15", 0),
            tda=f.get("td_accuracy", 0), tdd=f.get("td_defense", 0),
            sub=f.get("sub_avg_per_15", 0), fr=f.get("finish_rate", 0),
        ) for f in fighters])
        return np.hstack([features, styles])


class FightDatasetBuilder:
    """Builds (M, F) matchup feature matrix from fight history."""

    def __init__(self, repo: Optional[FeatureRepository] = None):
        self.repo = repo or FeatureRepository()

    def build(
        self,
        fights: list[dict],
        fighter_lookup: dict[str, dict],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Build features + labels for fights.

        Returns:
            features: (M, D) matrix
            labels: (M,) binary labels (1 = fighter_a won)
        """
        from intelligence.feature_engineering.matchup import MatchupFeatures
        mf = MatchupFeatures()

        m = len(fights)
        d = mf.dim + 2  # +2 for Elo diff + age diff
        features = np.zeros((m, d), dtype=np.float32)
        labels = np.zeros(m, dtype=np.float32)

        for i, fight in enumerate(fights):
            fa = fighter_lookup.get(fight["fighter_a_id"], {})
            fb = fighter_lookup.get(fight["fighter_b_id"], {})

            if fa and fb:
                matchup = mf.extract_pair(fa, fb)
                features[i, :len(matchup)] = matchup
                features[i, -2] = fa.get("elo_rating", 1500) - fb.get("elo_rating", 1500)
                features[i, -1] = fa.get("age", 30) - fb.get("age", 30)

            labels[i] = 1.0 if fight.get("winner_id") == fight.get("fighter_a_id") else 0.0

        return features, labels
