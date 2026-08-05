/** Fighters Mutations — favorite/unfavorite */

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
