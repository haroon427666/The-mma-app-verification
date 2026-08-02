/** Hooks barrel — re-exports from features */

export { useAuth } from './useAuth';
export { useNetwork } from './useNetwork';
export { useTheme } from './useTheme';
export {
  useHome, useLiveEvents, useTrendingFighters,
  useRecommendedFighters,
} from '@/features/home';
export {
  useFighterList, useFighterDetail, useFavoriteFighter,
  useFavoriteFighters, useFighterStats, useFightHistory, useSimilarFighters,
} from '@/features/fighters';
export { useEvents, useEvent } from '@/features/events';
export { useRankings } from '@/features/rankings';
export { useFightPrediction } from '@/features/predictions';
export { useRecommendations } from '@/features/recommendations';
export { useSearch } from '@/features/search';
export { useWatchlist } from '@/features/watchlist';
export { useNotifications } from '@/features/notifications';
export { useRefresh, screenRefreshes } from './useRefresh';
export { useRenderCount, thumbnailUrl, mediumUrl, defaultKeyExtractor, estimatedItemSize, fixedItemLayout, shallow } from './usePerformance';
export { useProfile } from '@/features/profile';
