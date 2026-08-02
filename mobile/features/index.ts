/** Mobile features — global barrel export (all 13 features, production wired) */

// ── Home ──
export { HomeScreen, useHome, useHomeStore, homeActions } from './home';
// ── Events ──
export { EventsStack, EventsScreen, EventDetailScreen, FightCardScreen, LiveEventScreen, ResultsScreen, EventStatisticsScreen, useEvents, useEvent, useWatchEvent, useFightCard, useCountdown, useEventsStore, eventsActions } from './events';
// ── Fighters ──
export { FightersStack, FightersScreen, FighterProfileScreen, FighterStatsScreen, FighterComparisonScreen, useFighterList, useFighterDetail, useFavoriteFighter, useFightersStore, fightersActions, WEIGHT_CLASSES } from './fighters';
// ── Rankings ──
export { RankingsStack, RankingsScreen, RankingHistoryScreen, useP4P, useDivisionRankings, useGOAT, useProspects, useRankingsStore, rankingsActions, rankingColors } from './rankings';
// ── Predictions ──
export { PredictionsStack, PredictionsDashboardScreen, FightPredictionScreen, PredictionReportScreen, MonteCarloScreen, PredictionHistoryScreen, SavedPredictionsScreen, ComparePredictionsScreen, useFightPrediction, usePredictionDashboard, usePredictionAccuracy, usePredictionsStore, predictionsActions, predictionKeys, predictionCache, predictionColors } from './predictions';
// ── Recommendations ──
export { RecommendationsStack, RecsScreen, useRecs, useRecTrending, useRecFeedback, useDismissRec, useRecStore, recActions, recKeys, recCache, recColors } from './recommendations/RecsModule';
// ── Search ──
export { SearchStack, SearchScreen, useSearch, useAutocomplete, useTrendingSearches, usePopularSearches, useSearchStore, searchActions, searchKeys, searchColors } from './search/SearchModule';
// ── Watchlist ──
export { WatchlistStack, WatchScreen, useWatchlist, useWatchReminders, useAddToWatchlist, useRemoveFromWatchlist, useWatchStore, watchKeys } from './watchlist/WatchModule';
// ── Notifications ──
export { NotificationsStack, NotifScreen, useNotifications, useUnreadCount, useMarkRead, useMarkAllRead, useDeleteNotif, useNotifStore, notifKeys, notifColors } from './notifications/NotifsModule';
// ── Profile + Settings ──
export { ProfileStack, ProfileScreen, useProfile, useUserStats, useSessions, useRevokeSession, useRevokeAllSessions, useDeleteAccount, useExportData, useProfileStore, profileActions, profileKeys } from './profile/ProfileModule';
// ── Onboarding ──
export { OnboardingScreen } from './onboarding';

// Shared domain types
export type * from './models';
