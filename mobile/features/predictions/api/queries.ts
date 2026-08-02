/** Predictions API + store */

import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { Prediction } from '../../models';

export function useFightPrediction(fightId: string) {
  return useQuery<Prediction>({
    queryKey: ['predictions', fightId],
    queryFn: async () => { const { data } = await api.get(`/v1/predictions/fight/${fightId}`); return data; },
    enabled: !!fightId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useEventPredictions(eventId: string) {
  return useQuery<Record<string, Prediction>>({
    queryKey: ['predictions', 'event', eventId],
    queryFn: async () => { const { data } = await api.get(`/v1/predictions/event/${eventId}`); return data; },
    enabled: !!eventId,
  });
}

export const usePredictionStore = create<{ selectedFightId: string | null }>(() => ({ selectedFightId: null }));
