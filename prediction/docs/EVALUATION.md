# Evaluation Guide

## Backtesting

Run `run_backtest()` to simulate predictions on historical fights.

```python
from prediction.evaluation.backtesting import run_backtest
results = run_backtest(fights, fighter_lookup, predictor)
print(f"Accuracy: {results['accuracy']}")
print(f"Log Loss: {results['log_loss']}")
print(f"Brier: {results['brier_score']}")
```

## Metrics

- **Accuracy:** % of correct winner predictions (>0.5 threshold)
- **Log Loss:** Calibrated probability error
- **Brier Score:** Mean squared error
- **Calibration Plot:** Predicted vs actual by probability bins

## Baseline Comparison

Always compare against:
- Always picking favorite (Elo > opponent) = ~65%
- Picking champion = ~70%
- Model target = >73%
