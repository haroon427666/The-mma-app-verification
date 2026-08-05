/** Query keys — centralized, namespaced, never hardcoded in hooks */

export const eventKeys = {
  all: ['events'] as const,
  lists: () => [...eventKeys.all, 'list'] as const,
  list: (filter: string) => [...eventKeys.lists(), filter] as const,
  details: () => [...eventKeys.all, 'detail'] as const,
  detail: (id: string) => [...eventKeys.details(), id] as const,
  live: () => [...eventKeys.all, 'live'] as const,
  upcoming: (limit?: number) => [...eventKeys.all, 'upcoming', limit] as const,
  past: () => [...eventKeys.all, 'past'] as const,
};

export const fightKeys = {
  all: (eventId: string) => ['events', eventId, 'fights'] as const,
  card: (eventId: string) => [...fightKeys.all(eventId), 'card'] as const,
  detail: (fightId: string) => ['fights', 'detail', fightId] as const,
};

export const watchlistKeys = {
  all: ['watchlist'] as const,
  events: () => [...watchlistKeys.all, 'events'] as const,
  event: (eventId: string) => [...watchlistKeys.events(), eventId] as const,
};
