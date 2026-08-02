/** Watchlist store — optimistic list of watched event IDs */

import { create } from 'zustand';

interface WatchlistState {
  watchedIds: Set<string>;
  isSyncing: boolean;
}

export const useWatchlistStore = create<WatchlistState>(() => ({
  watchedIds: new Set(),
  isSyncing: false,
}));

export const watchlistActions = {
  addOptimistic: (eventId: string) => useWatchlistStore.setState((s) => {
    const next = new Set(s.watchedIds); next.add(eventId);
    return { watchedIds: next };
  }),
  removeOptimistic: (eventId: string) => useWatchlistStore.setState((s) => {
    const next = new Set(s.watchedIds); next.delete(eventId);
    return { watchedIds: next };
  }),
  hydrate: (ids: string[]) => useWatchlistStore.setState({
    watchedIds: new Set(ids), isSyncing: false,
  }),
  setSyncing: (v: boolean) => useWatchlistStore.setState({ isSyncing: v }),
};
