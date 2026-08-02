/** Recommendations Module — complete barrel export */

// ── API + Repository ──
export { recommendationsApi, recommendationsRepo } from './api';
// ── Services + Hooks + Mutations ──
export { recommendationKeys, recommendationCache, recommendationAnalytics } from './api';
export { useRecommendations, useRecommendationsDashboard, useRecommendedFighters, useRecommendedEvents, useBecauseYouFollow, useBecauseYouWatched, useTrendingRecs, useHiddenGems, useSimilarFightersRec, useRecommendationMetrics } from './api';
export { useDismissRecommendation, useRecommendationFeedback } from './api';
export { useRecommendationStore, recommendationActions } from './api';
// ── Navigation ──
export { RecommendationsStack } from './navigation/RecommendationsStack';
export type { RecommendationsStackParamList } from './navigation/RecommendationsStack';
// ── Screens ──
export { RecommendationsScreen } from './screens';
// ── Theme + Charts + Errors ──
export { recommendationColors, MetricsChart, NoRecommendations } from './screens';
// ── Types ──
export type * from './types';
