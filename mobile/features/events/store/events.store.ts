/** Events store — event list state, selected event */

import { create } from 'zustand';
import type { EventFilter } from '../types';

interface EventsState {
  activeFilter: EventFilter;
  selectedPromotion: string | null;
  searchQuery: string;
  calendarDate: string | null;
  scrollPosition: number;
  dismissedIds: Set<string>;
}

export const useEventsStore = create<EventsState>(() => ({
  activeFilter: 'upcoming',
  selectedPromotion: null,
  searchQuery: '',
  calendarDate: null,
  scrollPosition: 0,
  dismissedIds: new Set(),
}));

export const eventsActions = {
  setFilter: (f: EventFilter) => useEventsStore.setState({ activeFilter: f }),
  setPromotion: (p: string | null) => useEventsStore.setState({ selectedPromotion: p }),
  setSearch: (q: string) => useEventsStore.setState({ searchQuery: q }),
  dismiss: (id: string) => useEventsStore.setState((s) => {
    const next = new Set(s.dismissedIds); next.add(id);
    return { dismissedIds: next };
  }),
};
