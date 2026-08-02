"""Feature Registry — every feature registered, versioned, typed, documented.

Professional ML systems always have this. No more undocumented columns.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    dtype: str
    version: int = 1
    description: str = ""
    category: str = ""
    range: tuple[float, float] | None = None
    source: str = ""
    deprecated: bool = False


FEATURE_REGISTRY: dict[str, FeatureSpec] = {
    # ── Physical ──────────────────────────────────────────────────────
    "age": FeatureSpec("age", "float32", 1, "Fighter age in years", "physical", (18, 50)),
    "height_cm": FeatureSpec("height_cm", "float32", 1, "Height in centimeters", "physical", (150, 220)),
    "reach_cm": FeatureSpec("reach_cm", "float32", 1, "Reach in centimeters", "physical", (150, 220)),
    "ape_index": FeatureSpec("ape_index", "float32", 1, "Reach minus height", "physical", (-20, 30)),
    "weight_kg": FeatureSpec("weight_kg", "float32", 1, "Fight weight in kilograms", "physical", (52, 130)),
    "age_performance_score": FeatureSpec("age_performance_score", "float32", 1, "Age curve score [0,1]", "physical", (0, 1)),

    # ── Striking ─────────────────────────────────────────────────────
    "slpm": FeatureSpec("slpm", "float32", 1, "Significant strikes landed per minute", "striking", (0, 8)),
    "striking_accuracy": FeatureSpec("striking_accuracy", "float32", 1, "Striking accuracy %", "striking", (0, 100)),
    "striking_defense": FeatureSpec("striking_defense", "float32", 1, "Striking defense %", "striking", (0, 100)),
    "sapm": FeatureSpec("sapm", "float32", 1, "Significant strikes absorbed per minute", "striking", (0, 8)),
    "striking_differential": FeatureSpec("striking_differential", "float32", 1, "SLpM minus SApM", "striking", (-8, 8)),
    "knockdown_rate": FeatureSpec("knockdown_rate", "float32", 1, "Knockdowns per fight", "striking", (0, 3)),

    # ── Grappling ────────────────────────────────────────────────────
    "td_avg_per_15": FeatureSpec("td_avg_per_15", "float32", 1, "Takedowns per 15 minutes", "grappling", (0, 6)),
    "td_accuracy": FeatureSpec("td_accuracy", "float32", 1, "Takedown accuracy %", "grappling", (0, 100)),
    "td_defense": FeatureSpec("td_defense", "float32", 1, "Takedown defense %", "grappling", (0, 100)),
    "sub_avg_per_15": FeatureSpec("sub_avg_per_15", "float32", 1, "Submission attempts per 15 min", "grappling", (0, 3)),
    "sub_win_rate": FeatureSpec("sub_win_rate", "float32", 1, "Submission win %", "grappling", (0, 1)),

    # ── Record ───────────────────────────────────────────────────────
    "win_rate": FeatureSpec("win_rate", "float32", 1, "Win percentage", "record", (0, 1)),
    "finish_rate": FeatureSpec("finish_rate", "float32", 1, "KO+Sub wins / total wins", "record", (0, 1)),
    "decision_rate": FeatureSpec("decision_rate", "float32", 1, "Decision wins / total wins", "record", (0, 1)),
    "streak": FeatureSpec("streak", "int32", 1, "Current win/loss streak", "record", (-20, 20)),
    "total_fights": FeatureSpec("total_fights", "int32", 1, "Total career fights", "record", (0, 100)),

    # ── Momentum ─────────────────────────────────────────────────────
    "momentum_score": FeatureSpec("momentum_score", "float32", 1, "Recent form score [0,1]", "momentum", (0, 1)),
    "trajectory_slope": FeatureSpec("trajectory_slope", "float32", 1, "Career trajectory slope", "momentum", (-1, 1)),
    "activity_rate": FeatureSpec("activity_rate", "float32", 1, "Fights per year [0,1]", "momentum", (0, 1)),

    # ── Quality ──────────────────────────────────────────────────────
    "win_quality": FeatureSpec("win_quality", "float32", 1, "Average quality of beaten opponents", "quality", (0, 1)),
    "opp_quality": FeatureSpec("opp_quality", "float32", 1, "Average quality of all opponents", "quality", (0, 1)),
    "championship_score": FeatureSpec("championship_score", "float32", 1, "Title fight pedigree [0,1]", "quality", (0, 1)),

    # ── Ranking ──────────────────────────────────────────────────────
    "elo_rating": FeatureSpec("elo_rating", "float32", 1, "Elo rating", "ranking", (1200, 2200)),
    "glicko_rating": FeatureSpec("glicko_rating", "float32", 1, "Glicko rating", "ranking", (1200, 2200)),
    "glicko_rd": FeatureSpec("glicko_rd", "float32", 1, "Glicko rating deviation", "ranking", (60, 350)),
    "composite_ranking": FeatureSpec("composite_ranking", "float32", 1, "Composite ranking score [0,1000]", "ranking", (0, 1000)),
    "rank_percentile": FeatureSpec("rank_percentile", "float32", 1, "Rank position as percentile", "ranking", (0, 1)),

    # ── Style ────────────────────────────────────────────────────────
    "striking_volume": FeatureSpec("striking_volume", "float32", 1, "Normalized striking volume", "style", (0, 1)),
    "grappling_volume": FeatureSpec("grappling_volume", "float32", 1, "Normalized grappling volume", "style", (0, 1)),
    "finishing_ability": FeatureSpec("finishing_ability", "float32", 1, "Finish rate in wins", "style", (0, 1)),
    "pressure_score": FeatureSpec("pressure_score", "float32", 1, "Forward pressure indicator", "style", (0, 1)),

    # ── Matchup ──────────────────────────────────────────────────────
    "reach_advantage": FeatureSpec("reach_advantage", "float32", 1, "A reach - B reach (normalized)", "matchup", (-1, 1)),
    "age_advantage": FeatureSpec("age_advantage", "float32", 1, "B age - A age (normalized)", "matchup", (-1, 1)),
    "elo_differential": FeatureSpec("elo_differential", "float32", 1, "A Elo - B Elo", "matchup", (-500, 500)),
    "style_contrast": FeatureSpec("style_contrast", "float32", 1, "L2 distance between style vectors", "matchup", (0, 2)),
    "h2h_record": FeatureSpec("h2h_record", "float32", 1, "Head-to-head record (A wins / total)", "matchup", (0, 1)),
}


def get_feature(name: str) -> Optional[FeatureSpec]:
    return FEATURE_REGISTRY.get(name)


def list_features(category: str | None = None) -> list[FeatureSpec]:
    features = list(FEATURE_REGISTRY.values())
    if category:
        features = [f for f in features if f.category == category]
    return sorted(features, key=lambda f: f.name)


def feature_names(category: str | None = None) -> list[str]:
    return [f.name for f in list_features(category)]
