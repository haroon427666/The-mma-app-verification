/** Fighters hooks */

import { useCallback } from 'react';
import {
  useFighters as useFightersQuery,
  useFighter,
  useFighterStats,
  useFightHistory,
  useSimilarFighters,
  useFavoriteFighters,
} from '../api/queries';
import { useFavoriteFighter } from '../api/mutations';
import { useFightersStore, fightersActions } from '../store/fightersStore';

export function useFighterList(weightClass?: string | null) {
  const query = useFightersQuery(weightClass);
  const { selectedDivision } = useFightersStore();
  return { ...query, selectedDivision, setDivision: fightersActions.setDivision };
}

export function useFighterDetail(id: string) {
  const fighter = useFighter(id);
  const stats = useFighterStats(id);
  const history = useFightHistory(id);
  const similar = useSimilarFighters(id);
  const { selectedTab } = useFightersStore();

  return {
    fighter: fighter.data,
    stats: stats.data,
    history: history.data,
    similar: similar.data,
    isLoading: fighter.isLoading,
    tab: selectedTab,
    setTab: fightersActions.setTab,
  };
}

export { useFavoriteFighter, useFavoriteFighters, useFighterStats, useFightHistory, useSimilarFighters };
