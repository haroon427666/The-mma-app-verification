/** Mutations — Watchlist and Reminder mutations with optimistic updates */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { watchlistRepo } from '../repository';
import { watchlistKeys } from '../services/queryKeys';
import { watchlistActions } from '../store/watchlist.store';
import { eventsAnalytics } from '../analytics/track';

export function useWatchEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (eventId: string) => { await watchlistRepo.add(eventId); return eventId; },
    onMutate: async (eventId) => {
      await qc.cancelQueries({ queryKey: watchlistKeys.events() });
      watchlistActions.addOptimistic(eventId);
      return { eventId };
    },
    onSuccess: (eventId) => eventsAnalytics.watchlistAdded(eventId),
    onError: (_err, eventId) => watchlistActions.removeOptimistic(eventId),
    onSettled: () => qc.invalidateQueries({ queryKey: watchlistKeys.events() }),
  });
}

export function useUnwatchEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (eventId: string) => { await watchlistRepo.remove(eventId); return eventId; },
    onMutate: async (eventId) => {
      await qc.cancelQueries({ queryKey: watchlistKeys.events() });
      watchlistActions.removeOptimistic(eventId);
      return { eventId };
    },
    onSuccess: (eventId) => eventsAnalytics.watchlistRemoved(eventId),
    onError: (_err, eventId) => watchlistActions.addOptimistic(eventId),
    onSettled: () => qc.invalidateQueries({ queryKey: watchlistKeys.events() }),
  });
}
