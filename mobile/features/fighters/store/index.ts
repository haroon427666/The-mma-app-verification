/** Fighters Stores — filters, comparison, favorites */

import { create } from 'zustand';
import type { FighterFilterType, FighterSortType, FighterTabKey } from '../types';

export const useFightersStore = create<{
  filter: FighterFilterType;
  sort: FighterSortType;
  selectedWeightClass: string | null;
  searchQuery: string;
  tab: FighterTabKey;
  scrollPosition: number;
}>(() => ({
  filter: 'all', sort: 'rank', selectedWeightClass: null,
  searchQuery: '', tab: 'overview', scrollPosition: 0,
}));

export const fightersActions = {
  setFilter: (f: FighterFilterType) => useFightersStore.setState({ filter: f }),
  setSort: (s: FighterSortType) => useFightersStore.setState({ sort: s }),
  setWeightClass: (wc: string | null) => useFightersStore.setState({ selectedWeightClass: wc }),
  setSearch: (q: string) => useFightersStore.setState({ searchQuery: q }),
  setTab: (t: FighterTabKey) => useFightersStore.setState({ tab: t }),
};

export const useCompareStore = create<{
  fighterA: string | null; fighterB: string | null; isComparing: boolean;
}>(() => ({ fighterA: null, fighterB: null, isComparing: false }));

export const compareActions = {
  setA: (id: string | null) => useCompareStore.setState({ fighterA: id }),
  setB: (id: string | null) => useCompareStore.setState({ fighterB: id }),
  clear: () => useCompareStore.setState({ fighterA: null, fighterB: null }),
};

export const useFavoritesStore = create<{ ids: Set<string> }>(() => ({ ids: new Set() }));
