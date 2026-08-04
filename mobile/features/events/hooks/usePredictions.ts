/** usePredictions — fight predictions for an event */

import { useQuery } from '@tanstack/react-query';
import { predictionsApi } from '../api/predictions.api';
import type { FightPrediction } from '../types';

export function usePredictions(eventId: string) {
  return useQuery({
    queryKey: ['events', 'predictions', eventId],
    queryFn: async () => { const { data } = await predictionsApi.forEvent(eventId); return data ?? {}; },
    staleTime: 30 * 60 * 1000,
    enabled: !!eventId,
  });
}

export function useFightPrediction(fightId: string) {
  return useQuery<FightPrediction | null>({
    queryKey: ['events', 'predictions', 'fight', fightId],
    queryFn: async () => { const { data } = await predictionsApi.forFight(fightId); return data ?? null; },
    staleTime: 30 * 60 * 1000,
    enabled: !!fightId,
  });
}
