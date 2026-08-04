/** Watchlist API + store */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';

export function useWatchlist() {
  return useQuery({
    queryKey: ['watchlist'],
    queryFn: async () => {
      const [{ data: events }, { data: fighters }] = await Promise.all([
        api.get('/v1/me/watchlist/events'), api.get('/v1/me/favorites/fighters'),
      ]);
      return { events: events.data ?? [], fighters: fighters.data ?? [] };
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useRemoveFavorite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fighterId: string) => api.delete(`/v1/me/favorites/fighters/${fighterId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  });
}

export const useWatchlistStore = create<{ selectedTab: 'events' | 'fighters' }>(() => ({ selectedTab: 'events' }));
