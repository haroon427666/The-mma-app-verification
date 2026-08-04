/** Fighters Mutations — favorites, unfavorite, follow, unfollow, compare */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { favoriteKeys } from '../services/queryKeys';
import { fighterAnalytics } from '../services/cache';

export function useFavoriteFighter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (fighterId: string) => { await api.post(`/v1/me/favorites/fighters/${fighterId}`); },
    onMutate: async (fighterId) => {
      await qc.cancelQueries({ queryKey: favoriteKeys.all });
      qc.setQueryData(favoriteKeys.check(fighterId), true);
    },
    onSuccess: (_data, id) => fighterAnalytics.favorited(id),
    onError: (_err, id) => qc.setQueryData(favoriteKeys.check(id), false),
    onSettled: () => qc.invalidateQueries({ queryKey: favoriteKeys.all }),
  });
}

export function useUnfavoriteFighter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (fighterId: string) => { await api.delete(`/v1/me/favorites/fighters/${fighterId}`); },
    onMutate: async (fighterId) => {
      await qc.cancelQueries({ queryKey: favoriteKeys.all });
      qc.setQueryData(favoriteKeys.check(fighterId), false);
    },
    onSuccess: (_data, id) => fighterAnalytics.unfavorited(id),
    onError: (_err, id) => qc.setQueryData(favoriteKeys.check(id), true),
    onSettled: () => qc.invalidateQueries({ queryKey: favoriteKeys.all }),
  });
}

export function useFollowFighter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fighterId: string) => api.post(`/v1/follows/fighters/${fighterId}`),
    onSettled: () => qc.invalidateQueries({ queryKey: ['follows'] }),
  });
}

export function useUnfollowFighter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fighterId: string) => api.delete(`/v1/follows/fighters/${fighterId}`),
    onSettled: () => qc.invalidateQueries({ queryKey: ['follows'] }),
  });
}

export function useCompareFighters() {
  return useMutation({
    mutationFn: async ({ fighterA, fighterB }: { fighterA: string; fighterB: string }) => {
      const { data } = await api.get(`/v1/predictions/matchup?fighter_a=${fighterA}&fighter_b=${fighterB}`);
      return data;
    },
    onSuccess: (_data, vars) => fighterAnalytics.compared(vars.fighterA, vars.fighterB),
  });
}
