/** Fighters store */

import { create } from 'zustand';
import type { Fighter } from '../../models';

interface FightersState {
  selectedDivision: string | null;
  selectedTab: string;
  comparisonFighter: Fighter | null;
  favoriteIds: Set<string>;
  scrollPosition: number;
}

export const useFightersStore = create<FightersState>(() => ({
  selectedDivision: null,
  selectedTab: 'overview',
  comparisonFighter: null,
  favoriteIds: new Set(),
  scrollPosition: 0,
}));

export const fightersActions = {
  setDivision: (d: string | null) => useFightersStore.setState({ selectedDivision: d }),
  setTab: (t: string) => useFightersStore.setState({ selectedTab: t }),
  setComparisonFighter: (f: Fighter | null) => useFightersStore.setState({ comparisonFighter: f }),
  toggleFavorite: (id: string) => useFightersStore.setState((s) => {
    const next = new Set(s.favoriteIds);
    next.has(id) ? next.delete(id) : next.add(id);
    return { favoriteIds: next };
  }),
};
