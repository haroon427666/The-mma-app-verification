/** Fighters module — barrel export */

// ── API ──
export { fightersApi, statsApi, historyApi, similarityApi, favoritesApi } from './api/fighters.api';

// ── Repository ──
export { fightersRepo, statsRepo, historyRepo, similarityRepo, favoritesRepo } from './repository';

// ── Services ──
export { fighterKeys, fighterStatsKeys, fighterHistoryKeys, similarityKeys, predictionKeys, favoriteKeys } from './services/queryKeys';
export { fighterCache, fighterAnalytics, useFighterOfflineStore } from './services/cache';
export { fighterDeeplinks, fighterSharing } from './services/deeplink';

// ── Mutations ──
export { useFavoriteFighter, useUnfavoriteFighter } from './mutations';

// ── Stores ──
export { useFightersStore, fightersActions, useCompareStore, compareActions, useFavoritesStore } from './store';

// ── Hooks ──
export { useFighters, useFighter, useStats, useHistory, useSimilarFighters, useIsFavorite } from './hooks';
export { useFighterList, useFighterDetail } from './hooks/useFighters';

// ── Navigation ──
export { FightersStack } from './navigation/FightersStack';
export type { FightersStackParamList } from './navigation/FightersStack';

// ── Screens ──
export { FightersScreen, FighterProfileScreen, FighterStatsScreen, FighterComparisonScreen, SimilarFightersScreen, AchievementsScreen, MediaScreen } from './screens';

// ── Components ──
export { FighterHeader, FighterRecord, FighterStats, FightHistoryRow, SimilarityCard, FavoriteButton } from './components';
export { FighterCardSkeleton, ProfileSkeleton, EmptyState, ErrorState } from './components/Skeletons';

// ── Charts ──
export { RadarChart, LineChart, MomentumChart } from './charts';

// ── Theme ──
export { fighterColors, fighterLabels, FighterAvatar, WEIGHT_CLASSES } from './theme';

// ── Types ──
export type * from './types';
