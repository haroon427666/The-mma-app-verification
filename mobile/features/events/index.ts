/** Events module — complete production barrel export (80+ symbol surface) */

// ── API ──
export { eventsApi } from './api/events.api';
export { fightsApi } from './api/fights.api';
export { watchlistApi } from './api/watchlist.api';

// ── Repository ──
export { eventsRepo, fightsRepo, watchlistRepo } from './repository';

// ── Services ──
export { eventKeys, fightKeys, watchlistKeys } from './services/queryKeys';

// ── Socket ──
export { liveFightSocket } from './socket/LiveFightSocket';

// ── Offline ──
export { eventsOfflineQueue } from './offline/queue';

// ── Analytics ──
export { eventsAnalytics } from './analytics/track';

// ── Stores ──
export { useEventsStore, eventsActions } from './store/events.store';
export { useFiltersStore, filtersActions } from './store/filters.store';
export { useWatchlistStore, watchlistActions } from './store/watchlist.store';

// ── Hooks ──
export {
  useEvents, useEvent, useUpcomingEvents, usePastEvents,
  useLiveEvents, useFightCard, useCountdown, useWatchlist,
} from './hooks';

// ── Mutations ──
export { useWatchEvent, useUnwatchEvent } from './mutations/useWatchEvent';

// ── Navigation ──
export { EventsStack } from './navigation/EventsStack';
export type { EventsStackParamList } from './navigation/EventsStack';

// ── Screens ──
export { EventsScreen } from './screens/EventsScreen';
export { EventDetailScreen } from './screens/EventDetailScreen';
export { FightCardScreen } from './screens/FightCardScreen';
export { LiveEventScreen } from './screens/LiveEventScreen';
export { ResultsScreen, EventStatisticsScreen } from './screens/ResultsScreen';

// ── Components (20 files) ──
export { EventCard } from './components/EventCard';
export { LiveBanner } from './components/LiveBanner';
export { Countdown } from './components/Countdown';
export { FightRow } from './components/FightRow';
export { FightCard } from './components/FightCard';
export { WatchlistButton } from './components/WatchlistButton';
export {
  VenueCard, BroadcastCard, PromotionBadge, FightResult,
  FightStatus, SectionHeader, LoadingCard, ErrorCard, EmptyState,
} from './components/SupportComponents';

// ── Detail Sections ──
export {
  EventHero, EventInformation, FightCardSection,
  BroadcastSection, VenueSection,
} from './detail';

// ── Images ──
export { CachedImage, FighterAvatar, CountryFlag, Poster, PromotionLogo } from './images';

// ── Skeletons ──
export {
  EventCardSkeleton, FightCardSkeleton, DetailSkeleton,
  ResultsSkeleton,
} from './skeletons';

// ── Animations ──
export { CountdownFlip, FightCardExpand, LivePulse } from './animations';

// ── Errors ──
export { EventNotFound, NetworkError } from './errors';

// ── Theme ──
export { eventColors } from './theme/eventColors';
export { fightColors } from './theme/fightColors';

// ── Accessibility ──
export { eventLabels } from './accessibility/labels';

// ── Utils ──
export { sortFightCard, groupBySegment } from './utils/fightSorter';
export { isLive, isUpcoming, isCompleted } from './utils/eventStatus';
export { formatEventDate, formatVenue, formatBroadcasters } from './utils/formatter';

// ── Types ──
export type * from './types';
