/** Filters store — promotion, weight class, date range */

import { create } from 'zustand';

interface FiltersState {
  promotions: string[];
  selectedPromotions: Set<string>;
  weightClasses: string[];
  selectedWeightClasses: Set<string>;
  dateFrom: string | null;
  dateTo: string | null;
  showTitleFightsOnly: boolean;
  sortBy: 'date' | 'popularity' | 'fightCount';
  sortOrder: 'asc' | 'desc';
}

export const useFiltersStore = create<FiltersState>(() => ({
  promotions: ['UFC', 'ONE Championship', 'PFL', 'Bellator', 'Rizin'],
  selectedPromotions: new Set(),
  weightClasses: [],
  selectedWeightClasses: new Set(),
  dateFrom: null,
  dateTo: null,
  showTitleFightsOnly: false,
  sortBy: 'date',
  sortOrder: 'asc',
}));

export const filtersActions = {
  togglePromotion: (p: string) => useFiltersStore.setState((s) => {
    const next = new Set(s.selectedPromotions);
    next.has(p) ? next.delete(p) : next.add(p);
    return { selectedPromotions: next };
  }),
  toggleWeightClass: (wc: string) => useFiltersStore.setState((s) => {
    const next = new Set(s.selectedWeightClasses);
    next.has(wc) ? next.delete(wc) : next.add(wc);
    return { selectedWeightClasses: next };
  }),
  setDateRange: (from: string | null, to: string | null) => useFiltersStore.setState({ dateFrom: from, dateTo: to }),
  toggleTitleFights: () => useFiltersStore.setState((s) => ({ showTitleFightsOnly: !s.showTitleFightsOnly })),
  setSort: (sortBy: FiltersState['sortBy']) => useFiltersStore.setState({ sortBy }),
  clearAll: () => useFiltersStore.setState({
    selectedPromotions: new Set(), selectedWeightClasses: new Set(),
    dateFrom: null, dateTo: null, showTitleFightsOnly: false,
  }),
};
