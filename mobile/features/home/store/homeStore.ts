/** Home store — local UI state */

import { create } from 'zustand';
import type { HomeState } from '../types';

export const useHomeStore = create<HomeState>(() => ({
  dismissedCards: new Set(),
  selectedPromotion: null,
  scrollPosition: 0,
  lastRefreshAt: null,
}));

export const homeActions = {
  dismissCard: (id: string) => useHomeStore.setState((s) => {
    const next = new Set(s.dismissedCards); next.add(id);
    return { dismissedCards: next };
  }),
  setPromotion: (promotion: string | null) => useHomeStore.setState({ selectedPromotion: promotion }),
  setScrollPosition: (pos: number) => useHomeStore.setState({ scrollPosition: pos }),
  markRefreshed: () => useHomeStore.setState({ lastRefreshAt: new Date().toISOString() }),
};
