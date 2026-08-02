/** Rankings Module — Complete barrel export (70+ symbols) */

// ── API ──
export { rankingsApi } from './api/rankings.api';

// ── Repository ──
export { rankingsRepo } from './repository';

// ── Services ──
export { rankingKeys, rankingCache, rankingAnalytics, rankingDeeplinks } from './services';

// ── Hooks ──
export { useP4P, useDivisionRankings, useRankingHistory, useGOAT, useProspects, useRankingMovement, useStreaks, useChampions, useChampionsHistory, useTitleDefenses, useEloRankings, useCompositeRankings, useFavoriteRanking } from './hooks';

// ── Stores ──
export { useRankingsStore, rankingsActions, useRankingsOffline } from './stores';

// ── Navigation ──
export { RankingsStack } from './navigation/RankingsStack';
export type { RankingsStackParamList } from './navigation/RankingsStack';

// ── Screens ──
export { RankingsScreen, RankingHistoryScreen, ChampionHistoryScreen, TitleDefensesScreen, PoundForPoundScreen, DivisionRankingsScreen, RankMovementScreen, GOATRankingsScreen, ProspectsScreen, CompareRankingsScreen } from './screens';

// ── Components ──
export { RankingCard, ChampionCard, DivisionSelector, MovementArrow, RankBadge, StreakBadge, EloBadge, CompositeBadge, RankingsSkeleton, RankingEmpty, RankingError } from './components';

// ── Theme + Charts + Utils ──
export { rankingColors, WEIGHT_CLASSES, rankingLabels, RankingNotFound, RankProgressionChart, MovementTimelineChart, formatMovement, getTrajectoryColor, sortByRank, sortByELO } from './theme';

// ── Types ──
export type * from './types';
