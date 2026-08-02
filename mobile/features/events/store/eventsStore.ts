/** Events store */

import { create } from 'zustand';

interface EventsState {
  selectedFilter: 'upcoming' | 'past' | 'live';
  selectedPromotion: string | null;
  watchedEventIds: Set<string>;
}

export const useEventsStore = create<EventsState>(() => ({
  selectedFilter: 'upcoming',
  selectedPromotion: null,
  watchedEventIds: new Set(),
}));

export const eventsActions = {
  setFilter: (f: 'upcoming' | 'past' | 'live') => useEventsStore.setState({ selectedFilter: f }),
  setPromotion: (p: string | null) => useEventsStore.setState({ selectedPromotion: p }),
  toggleWatched: (id: string) => useEventsStore.setState((s) => {
    const next = new Set(s.watchedEventIds);
    next.has(id) ? next.delete(id) : next.add(id);
    return { watchedEventIds: next };
  }),
};
