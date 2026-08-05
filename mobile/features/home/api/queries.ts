/** Home queries — TanStack Query hooks */

import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { homeEndpoints } from './endpoints';
import type { HomeFeed, Event, Fighter } from '../../models';

export function useHomeFeed() {
  return useQuery<HomeFeed>({
    queryKey: ['home', 'feed'],
    queryFn: async () => {
      const [{ data: live }, { data: upcoming },
            { data: recs }, { data: titles }] = await Promise.all([
        api.get(homeEndpoints.live),
        api.get(homeEndpoints.upcoming),
        api.get(homeEndpoints.recommendedFighters),
        api.get(homeEndpoints.titleFights),
      ]);
      return {
        liveEvents: live?.data ?? [],
        upcomingEvents: upcoming?.data ?? [],
        trendingFighters: [],
        recommendedFighters: recs?.data ?? [],
        upcomingTitleFights: titles?.data ?? [],
        predictionHighlights: [],
        recentRankingChanges: [],
      };
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useLiveEvents() {
  return useQuery<Event[]>({
    queryKey: ['home', 'live'],
    queryFn: async () => { const { data } = await api.get(homeEndpoints.live); return data.data ?? []; },
    staleTime: 30 * 1000,
    refetchInterval: 30_000,
  });
}

export function useRecommendedFighters() {
  return useQuery<Fighter[]>({
    queryKey: ['home', 'recommendedFighters'],
    queryFn: async () => { const { data } = await api.get(homeEndpoints.recommendedFighters); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });
}
