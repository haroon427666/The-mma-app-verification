/** Recommendations Module — barrel export */

// ── API / Repository / Services / Hooks / Mutations / Store (consolidated in ./api) ──
export {
  recommendationsApi,
  recommendationsRepo,
  recommendationKeys,
  recommendationCache,
  recommendationAnalytics,
  useRecommendationStore,
  recommendationActions,
  useRecommendations,
  useRecommendationsDashboard,
  useRecommendedFighters,
  useRecommendedEvents,
  useBecauseYouFollow,
  useBecauseYouWatched,
  useTrendingRecs,
  useHiddenGems,
  useSimilarFightersRec,
  useRecommendationMetrics,
  useDismissRecommendation,
  useRecommendationFeedback,
} from './api';

// ── Screens / Stack (consolidated in ./RecsModule) ──
export { RecommendationsStack, RecsScreen, recColors, recsRepo, recKeys, recCache, useRecs, useRecFighters, useRecEvents, useRecTrending, useRecDiscover, useRecBecause, useRecFeedback, useDismissRec, useRecStore, recActions } from './RecsModule';

// ── Types ──
export type * from './types';
