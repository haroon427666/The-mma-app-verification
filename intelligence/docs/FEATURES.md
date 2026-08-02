# Intelligence Platform — Features Reference

## Registered Features (39 total)

| Category | Count | Features |
|---|---|---|
| **physical** | 6 | age, height_cm, reach_cm, ape_index, weight_kg, age_performance_score |
| **striking** | 6 | slpm, striking_accuracy, striking_defense, sapm, striking_differential, knockdown_rate |
| **grappling** | 5 | td_avg_per_15, td_accuracy, td_defense, sub_avg_per_15, sub_win_rate |
| **record** | 5 | win_rate, finish_rate, decision_rate, streak, total_fights |
| **momentum** | 3 | momentum_score, trajectory_slope, activity_rate |
| **quality** | 3 | win_quality, opp_quality, championship_score |
| **ranking** | 5 | elo_rating, glicko_rating, glicko_rd, composite_ranking, rank_percentile |
| **style** | 4 | striking_volume, grappling_volume, finishing_ability, pressure_score |
| **matchup** | 5 | reach_advantage, age_advantage, elo_differential, style_contrast, h2h_record |

## Feature Versioning

All features are versioned. Add new features with version=2+.
Never remove features — deprecate them.

## Adding a Feature

```python
from intelligence.feature_store.registry import FEATURE_REGISTRY, FeatureSpec

FEATURE_REGISTRY["my_feature"] = FeatureSpec(
    name="my_feature", dtype="float32", version=1,
    description="My new feature", category="physical",
    range=(0, 1), source="computed",
)
```
