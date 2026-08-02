/** Rankings Stores */

import { create } from 'zustand';
import type { RankingView, SortRankingBy, MovementDirection } from '../types';

export const useRankingsStore = create<{
  view: RankingView;
  selectedDivision: string;
  sortBy: SortRankingBy;
  movementDirection: MovementDirection;
  pinnedDivisions: Set<string>;
}>(() => ({
  view: 'p4p', selectedDivision: 'Heavyweight',
  sortBy: 'rank', movementDirection: 'all',
  pinnedDivisions: new Set(),
}));

export const rankingsActions = {
  setView: (v: RankingView) => useRankingsStore.setState({ view: v }),
  setDivision: (d: string) => useRankingsStore.setState({ selectedDivision: d, view: 'division' }),
  setSort: (s: SortRankingBy) => useRankingsStore.setState({ sortBy: s }),
  setMovement: (m: MovementDirection) => useRankingsStore.setState({ movementDirection: m }),
  togglePin: (d: string) => useRankingsStore.setState((s) => {
    const next = new Set(s.pinnedDivisions);
    next.has(d) ? next.delete(d) : next.add(d);
    return { pinnedDivisions: next };
  }),
};

export const useRankingsMutations = create<{
  favoritedFighters: Set<string>;
}>(() => ({ favoritedFighters: new Set() }));

// Offline cache store
export const useRankingsOffline = create<{
  lastSyncedAt: string | null; isStale: boolean;
}>(() => ({ lastSyncedAt: null, isStale: false }));
