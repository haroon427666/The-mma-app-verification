/** Rankings API + store */

import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { Ranking } from '../../models';

const DIVISIONS = ['Pound for Pound', 'Heavyweight', 'Light Heavyweight', 'Middleweight', 'Welterweight', 'Lightweight', 'Featherweight', 'Bantamweight', 'Flyweight', "Women's Bantamweight", "Women's Flyweight", "Women's Strawweight"] as const;

export function useRankings(division: string) {
  return useQuery<Ranking[]>({
    queryKey: ['rankings', division],
    queryFn: async () => {
      const url = division === 'Pound for Pound'
        ? '/v1/rankings/p4p'
        : `/v1/rankings/${encodeURIComponent(division)}`;
      const { data } = await api.get(url); return data.data ?? [];
    },
    staleTime: 10 * 60 * 1000,
  });
}

export const useRankingsStore = create<{ division: string }>(() => ({ division: 'Pound for Pound' }));
export const rankingsActions = { setDivision: (d: string) => useRankingsStore.setState({ division: d }) };
export { DIVISIONS };
