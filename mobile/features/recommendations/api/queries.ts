/** Recommendations API + store */

import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { Recommendation } from '../../models';

export function useRecommendations() {
  return useQuery<Recommendation[]>({
    queryKey: ['recommendations'],
    queryFn: async () => { const { data } = await api.get('/v1/recommendations?limit=20'); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });
}

export function useRecommendedFightersList() {
  return useQuery({ queryKey: ['recommendations', 'fighters'], queryFn: async () => {
    const { data } = await api.get('/v1/recommendations/fighters?limit=10'); return data.data ?? [];
  }, staleTime: 5 * 60 * 1000 });
}

export function useRecommendedEvents() {
  return useQuery({ queryKey: ['recommendations', 'events'], queryFn: async () => {
    const { data } = await api.get('/v1/recommendations/events?limit=5'); return data.data ?? [];
  }, staleTime: 10 * 60 * 1000 });
}

export const useRecommendationStore = create<{ dismissedIds: Set<string> }>(() => ({ dismissedIds: new Set() }));
