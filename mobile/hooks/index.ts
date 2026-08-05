/** Hooks barrel — re-exports from features */

export { useAuth } from './useAuth';
export { useNetwork } from './useNetwork';
export { useTheme } from './useTheme';
export {
  useHome, useLiveEvents,
  useRecommendedFighters,
} from '@/features/home';
export {
  useFighters, useFighter, useFavoriteFighter,
  useStats, useHistory, useSimilarFighters,
} from '@/features/fighters';
export { useEvents, useEvent } from '@/features/events';
export { useSearch } from '@/features/search';
export { useWatchlist } from '@/features/watchlist';
export { useNotifications } from '@/features/notifications';
export { useRefresh, screenRefreshes } from './useRefresh';
export { useRenderCount, thumbnailUrl, mediumUrl, defaultKeyExtractor, estimatedItemSize, fixedItemLayout, shallow } from './usePerformance';
