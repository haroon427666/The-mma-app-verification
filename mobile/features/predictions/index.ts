/** Predictions Module — barrel export */

export type * from './types';

// ── API / Repository / Services / Store / Hooks (consolidated in ./api) ──
export {
  predictionsApi,
  predictionsRepo,
  predictionKeys,
  predictionCache,
  predictionAnalytics,
  predictionDeeplinks,
  usePredictionStore,
  predictionActions,
  useFightPrediction,
  useEventPredictions,
  usePredictionDashboard,
  usePredictionHighlights,
  usePredictionHistory,
  usePredictionAccuracy,
  useMatchupPrediction,
  useSavedPredictions,
  useSavePrediction,
  useUnsavePrediction,
} from './api';

// ── Supplemental hooks (defined in ./hooks/usePredictions) ──
export {
  useMonteCarlo,
  usePredictionFactors,
  usePredictionOdds,
  useSharePrediction,
} from './hooks/usePredictions';

// ── Navigation ──
export { PredictionsStack } from './navigation/PredictionsStack';
export type { PredictionsStackParamList } from './navigation/PredictionsStack';

// ── Screens ──
export {
  PredictionsDashboardScreen,
  FightPredictionScreen,
  PredictionReportScreen,
  MonteCarloScreen,
  PredictionHistoryScreen,
  SavedPredictionsScreen,
  ComparePredictionsScreen,
} from './screens/PredictionsScreen';

// ── Components ──
export {
  WinProbabilityCard,
  ConfidenceBadge,
  FinishProbabilityBars,
  FactorsList,
  MonteCarloCard,
  PredictionOddsCard,
  AccuracyCard,
  PredictionCard,
  PredictionSkeleton,
  PredictionEmpty,
  PredictionUnavailable,
} from './components/PredictionsComponents';

// ── Theme ──
export { predictionColors, predictionLabels } from './components/PredictionsComponents';

// ── Store ──
export { usePredictionsStore, predictionsActions } from './stores/predictions.store';
