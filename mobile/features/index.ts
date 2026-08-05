/** Mobile features — global barrel export (all production-wired features) */

// ── Home ──
export { HomeScreen, useHome, useHomeStore, homeActions } from './home';
// ── Events ──
export { EventsStack, EventsScreen, EventDetailScreen, FightCardScreen, LiveEventScreen, ResultsScreen, EventStatisticsScreen, useEvents, useEvent, useWatchEvent, useFightCard, useCountdown, useEventsStore, eventsActions } from './events';
// ── Fighters ──
export { FightersStack, FightersScreen, FighterProfileScreen, FighterStatsScreen, FighterComparisonScreen, useFighterList, useFighterDetail, useFavoriteFighter, useFightersStore, fightersActions, WEIGHT_CLASSES } from './fighters';
// ── Rankings ──
export { RankingsStack, RankingsScreen, useP4P, useDivisionRankings, useGOAT, useProspects, useRankingsStore, rankingsActions, rankingColors } from './rankings';
// ── Search ──
export { SearchStack, SearchScreen, useSearch, useAutocomplete, useTrendingSearches, usePopularSearches, useSearchStore, searchActions, searchKeys, searchColors } from './search/SearchModule';
// ── Watchlist ──
export { WatchlistStack, WatchScreen, useWatchlist, useAddToWatchlist, useRemoveFromWatchlist, useWatchStore, watchKeys } from './watchlist/WatchModule';
// ── Notifications ──
export { NotificationsStack, NotifScreen, useNotifications, useUnreadCount, useMarkRead, useMarkAllRead, useDeleteNotif, useNotifStore, notifKeys, notifColors } from './notifications/NotifsModule';
// ── Profile + Settings ──
export { ProfileStack, ProfileScreen, useProfile, useSessions, useRevokeSession, useRevokeAllSessions, useDeleteAccount, useProfileStore, profileActions, profileKeys } from './profile/ProfileModule';
// ── Onboarding ──
export { OnboardingScreen } from './onboarding';

// Shared domain types
export type * from './models';
