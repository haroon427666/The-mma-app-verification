/** useWatchlist — optimistic add/remove with rollback */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { watchlistApi } from '../api/watchlist.api';
import { useWatchlistStore, watchlistActions } from '../store/watchlist.store';

export function useWatchlist(eventId?: string) {
  const qc = useQueryClient();
  const { watchedIds } = useWatchlistStore();

  const listQuery = useQuery({
    queryKey: ['watchlist', 'events'],
    queryFn: async () => { const { data } = await watchlistApi.list(); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });

  const isWatched = eventId ? watchedIds.has(eventId) : false;

  const toggle = useMutation({
    mutationFn: async (id: string) => {
      const isW = watchedIds.has(id);
      if (isW) await watchlistApi.remove(id);
      else await watchlistApi.add(id);
      return { id, wasWatched: isW };
    },
    onMutate: async ({ id }: { id: string }) => {
      await qc.cancelQueries({ queryKey: ['watchlist'] });
      const isW = watchedIds.has(id);
      if (isW) watchlistActions.removeOptimistic(id);
      else watchlistActions.addOptimistic(id);
      return { isW };
    },
    onError: (_err, { id }, ctx) => {
      if (ctx?.isW) watchlistActions.addOptimistic(id);
      else watchlistActions.removeOptimistic(id);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  });

  return { isWatched, list: listQuery.data ?? [], toggle: () => eventId && toggle.mutate(eventId) };
}
