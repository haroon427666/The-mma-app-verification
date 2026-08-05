/** Fighters module — complete barrel export (80+ symbols) */

// ── API ──
export { fightersApi, statsApi, historyApi, rankingsApi, similarityApi, predictionApi, recommendationApi } from './api/fighters.api';

// ── Repository ──
export { fightersRepo, statsRepo, historyRepo, similarityRepo, predictionRepo, recommendationRepo } from './repository';

// ── Services ──
export { fighterKeys, fighterStatsKeys, fighterHistoryKeys, similarityKeys, predictionKeys, favoriteKeys } from './services/queryKeys';
export { fighterCache, fighterAnalytics, useFighterOfflineStore } from './services/cache';
export { fighterDeeplinks, fighterSharing } from './services/deeplink';

// ── Mutations ──
export { useFavoriteFighter, useUnfavoriteFighter, useFollowFighter, useUnfollowFighter, useCompareFighters } from './mutations';

// ── Stores ──
export { useFightersStore, fightersActions, useCompareStore, compareActions, useFavoritesStore } from './store';

// ── Hooks ──
export { useFighters, useFighter, useStats, useHistory, useSimilarFighters, useStyleAnalysis, usePredictions, useIsFavorite, useRankHistory } from './hooks';
export { useFighterList, useFighterDetail } from './hooks/useFighters';

// ── Navigation ──
export { FightersStack } from './navigation/FightersStack';
export type { FightersStackParamList } from './navigation/FightersStack';

// ── Screens ──
export { FightersScreen, FighterProfileScreen, FighterStatsScreen, FighterComparisonScreen, SimilarFightersScreen, AchievementsScreen, MediaScreen } from './screens';

// ── Components ──
export { FighterHeader, FighterRecord, FighterStats, FightHistoryRow, SimilarityCard, FighterStyleBadge, RankMovement, FavoriteButton } from './components';
export { FighterCardSkeleton, ProfileSkeleton, EmptyState, ErrorState } from './components/Skeletons';

// ── Charts ──
export { RadarChart, LineChart, MomentumChart } from './charts';

// ── Theme ──
export { fighterColors, fighterLabels, FighterAvatar, WEIGHT_CLASSES } from './theme';

// ── Types ──
export type * from './types';
