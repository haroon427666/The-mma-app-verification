# Calibration Guide

## What is calibration?

If the model says 70% win probability, the fighter should actually win ~70% of the time.

## Metrics

- **Brier Score:** Mean squared error between predicted probability and actual outcome. Lower = better.
  - < 0.15: Excellent
  - < 0.20: Good
  - < 0.25: Fair
  - > 0.25: Poor

- **Log Loss:** Penalizes overconfident wrong predictions heavily.
  - < 0.50: Good
  - > 0.70: Needs improvement

## When to recalibrate

- After every major fight weekend
- After retraining the model
- If calibration drifts > 0.02 Brier points
