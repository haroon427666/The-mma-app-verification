# Prediction Platform — Model Architecture

## Fight Winner Prediction

**Primary model:** XGBoost classifier with 14 features.
**Fallback:** Elo + momentum + quality heuristic.

**Features:**
1. streak_diff — win/loss streak differential
2. elo_diff — Elo rating differential
3. age_diff — age differential (negative = A younger)
4. reach_diff — reach differential
5. finish_rate_a — fighter A finish rate
6. finish_rate_b — fighter B finish rate
7. momentum_a — fighter A momentum score
8. momentum_b — fighter B momentum score
9. win_quality_a — fighter A win quality
10. win_quality_b — fighter B win quality
11. championship_a — fighter A championship score
12. championship_b — fighter B championship score
13. striking_diff — SLpM differential
14. grappling_diff — TDs per 15 differential

## Finish Prediction

Multi-class: KO/TKO, Submission, Decision.
Features: finish_rate, ko_rate, sub_rate for both fighters.

## Round Prediction

Exponential decay model based on finish rate.
3 rounds (non-title) or 5 rounds (title/main event).

## Calibration

Platt scaling / isotonic binning.
Brier score < 0.15 = Excellent calibration.
