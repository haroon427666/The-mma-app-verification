# Predictions Architecture

## Layer Diagram
```
Navigation (9 screens)
  ↓
Screens (Dashboard, Fight, History, Saved, Compare, Report, MonteCarlo, Confidence, Style)
  ↓
Hooks (useFightPrediction, useDashboard, useHistory, etc.)
  ↓
Repository (predictionsRepo → 10 functions)
  ↓
API (predictionsApi → 10 endpoints → backend → prediction/ package)
```

## Integration with prediction/ package

The backend wraps the `prediction/` package from Phase 11.3:
- `FightPredictor` → winner probability
- `FinishPredictor` → KO/Sub/Dec probabilities
- `RoundPredictor` → 5-round distribution
- `MethodPredictor` → specific methods
- `MonteCarloSimulator` → 100K simulations
- `ConfidenceScorer` → 0-100 confidence score
- `StyleAnalysis` → style matchup engine

## State Ownership
| Store | Owns |
|---|---|
| `predictionStore` | view, sortBy, savedIds |
| TanStack Query | All prediction data |
