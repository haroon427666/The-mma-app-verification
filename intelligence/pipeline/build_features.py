#!/usr/bin/env python3
"""build_features.py — offline pipeline: computes all features and stores them.

Called by scheduler or manually. Produces the feature snapshot.
"""

import sys
import time
import numpy as np

from intelligence.feature_store.repository import FeatureRepository
from intelligence.feature_store.registry import FEATURE_REGISTRY, feature_names
from intelligence.feature_engineering.striking import StrikingFeatures
from intelligence.feature_engineering.grappling import GrapplingFeatures
from intelligence.feature_engineering.physical import PhysicalFeatures
from intelligence.feature_engineering.momentum import MomentumFeatures
from intelligence.feature_engineering.career import CareerFeatures


def build_all_features(fighters: list[dict]) -> FeatureRepository:
    repo = FeatureRepository()
    pipes = [
        ("striking", StrikingFeatures()),
        ("grappling", GrapplingFeatures()),
        ("physical", PhysicalFeatures()),
        ("momentum", MomentumFeatures()),
        ("career", CareerFeatures()),
    ]

    for fighter in fighters:
        fid = fighter.get("id", "")
        if not fid:
            continue

        features = {}
        for name, pipe in pipes:
            vec = pipe.extract(fighter)
            for i in range(pipe.dim):
                features[f"{name}_{i}"] = float(vec[i])

        # Named features
        features.update(_extract_named_features(fighter))
        repo.put(f"fighter:{fid}", features)

    return repo


def _extract_named_features(f: dict) -> dict:
    w, l = f.get("wins", 0), f.get("losses", 0)
    total = w + l + f.get("draws", 0)
    ko = f.get("ko_wins", 0); sub = f.get("sub_wins", 0)
    return {
        "age": f.get("age", 30),
        "height_cm": f.get("height_cm", 178),
        "reach_cm": f.get("reach_cm", 183),
        "weight_kg": f.get("weight_kg", 77),
        "ape_index": f.get("reach_cm", 183) - f.get("height_cm", 178),
        "slpm": f.get("sig_strikes_landed_per_min", 0),
        "striking_accuracy": f.get("sig_strikes_accuracy_pct", 0),
        "striking_defense": f.get("sig_strikes_defense_pct", 0),
        "sapm": f.get("sig_strikes_absorbed_per_min", 0),
        "td_avg_per_15": f.get("takedown_avg_per_15min", 0),
        "td_accuracy": f.get("takedown_accuracy_pct", 0),
        "td_defense": f.get("takedown_defense_pct", 0),
        "sub_avg_per_15": f.get("submission_avg_per_15min", 0),
        "sub_win_rate": sub / max(w, 1),
        "win_rate": w / max(total, 1),
        "finish_rate": (ko + sub) / max(w, 1),
        "decision_rate": (w - ko - sub) / max(w, 1),
        "streak": f.get("streak", 0),
        "total_fights": total,
    }


if __name__ == "__main__":
    print("Feature pipeline — import and use programmatically")
