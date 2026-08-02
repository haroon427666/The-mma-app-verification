/** Advanced Prediction — hooks + index */
import { useState, useCallback } from 'react';
import { ensembleLearner, monteCarlo, calibrationEngine, modelEvaluator, predAnalytics, predictionModels } from './PredictionEngine';
import type { PredictionInput, PredictionOutput, PredictionModelType, EnsembleWeights } from './PredictionEngine';

export function usePrediction() {
  const [result, setResult] = useState<PredictionOutput | null>(null);
  const [loading, setLoading] = useState(false);

  const predict = useCallback(async (input: PredictionInput, models?: PredictionModelType[]) => {
    setLoading(true); try { const r = await ensembleLearner.predict(input, models); setResult(r); return r; } finally { setLoading(false); }
  }, []);

  const simulate = useCallback(async (input: PredictionInput, iterations?: number) => {
    return monteCarlo.simulate(input, iterations);
  }, []);

  return { result, predict, simulate, loading, calibration: () => calibrationEngine.calculate() };
}

export function useModelComparison() {
  const [comparison, setComparison] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const compare = useCallback(async () => { setLoading(true); try { setComparison(modelEvaluator.compare()); } finally { setLoading(false); } }, []);
  return { comparison, compare, loading };
}

/*
## Advanced Prediction Platform

### Ensemble Model Architecture
```
PredictionInput { fighterA, fighterB, weightClass, ... }
  → Neural Network (0.20) → probA
  → Gradient Boosting (0.20) → probA
  → XGBoost (0.20) → probA
  → Random Forest (0.10) → probA
  → ELO (0.10) → probA
  → Bayesian (0.05) → probA
  → Glicko (0.05) → probA
  → Monte Carlo (0.05) → 10000 simulations
  → Weighted Ensemble → PredictionOutput
```

### Output Fields
- winnerId, probabilityA, confidence
- Method probabilities (KO/TKO, submission, decision)
- Round probabilities
- SHAP-style contributing factors
- Calibration score

### Hooks
- usePrediction() → predict, simulate Monte Carlo
- useModelComparison() → compare all 9 models
*/

export { ensembleLearner, monteCarlo, calibrationEngine, modelEvaluator, predAnalytics, predictionModels, confidenceLabel, defaultEnsembleWeights } from './PredictionEngine';
export type { PredictionModelType, WinMethod, PredictionConfidence, FighterStats, PredictionInput, PredictionOutput, EnsembleWeights, CalibrationCurve, ModelEvaluation } from './PredictionEngine';
