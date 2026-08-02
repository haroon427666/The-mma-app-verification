/** Fighters mutations */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import { fighterEndpoints } from './endpoints';

export function useFavoriteFighter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ fighterId, favorite }: { fighterId: string; favorite: boolean }) => {
      if (favorite) await api.post(fighterEndpoints.favorite(fighterId));
      else await api.delete(fighterEndpoints.favorite(fighterId));
    },
    onMutate: async ({ fighterId, favorite }) => {
      await qc.cancelQueries({ queryKey: ['fighters', 'favorites'] });
      const prev = qc.getQueryData(['fighters', 'favorites']);
      qc.setQueryData(['fighters', 'favorites'], (old: any) => {
        if (!old) return old;
        return favorite ? [...old, { id: fighterId }] : old.filter((f: any) => f.id !== fighterId);
      });
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(['fighters', 'favorites'], ctx.prev);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['fighters', 'favorites'] });
      qc.invalidateQueries({ queryKey: ['fighters', 'detail'] });
    },
  });
}
