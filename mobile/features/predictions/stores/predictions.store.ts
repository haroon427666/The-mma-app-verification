/** Predictions Store — view state, sort, saved IDs */

import { create } from 'zustand';
import type { PredictionView, PredictionSort } from '../types';

interface PredictionsState {
  view: PredictionView;
  sortBy: PredictionSort;
  savedIds: Set<string>;
  selectedFightId: string | null;
}

export const usePredictionsStore = create<PredictionsState>(() => ({
  view: 'dashboard',
  sortBy: 'confidence',
  savedIds: new Set(),
  selectedFightId: null,
}));

export const predictionsActions = {
  setView: (v: PredictionView) => usePredictionsStore.setState({ view: v }),
  setSort: (s: PredictionSort) => usePredictionsStore.setState({ sortBy: s }),
  addSaved: (id: string) => usePredictionsStore.setState((st) => {
    const next = new Set(st.savedIds); next.add(id);
    return { savedIds: next };
  }),
  removeSaved: (id: string) => usePredictionsStore.setState((st) => {
    const next = new Set(st.savedIds); next.delete(id);
    return { savedIds: next };
  }),
  selectFight: (id: string | null) => usePredictionsStore.setState({ selectedFightId: id }),
};
