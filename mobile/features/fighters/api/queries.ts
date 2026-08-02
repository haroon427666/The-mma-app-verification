/** Fighters queries — TanStack Query hooks */

import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { fighterEndpoints } from './endpoints';
import type { Fighter } from '../../models';

export function useFighters(weightClass?: string | null) {
  return useQuery<Fighter[]>({
    queryKey: ['fighters', 'list', weightClass],
    queryFn: async () => {
      const { data } = await api.get(fighterEndpoints.list(weightClass ?? undefined));
      return data.data ?? [];
    },
    staleTime: 10 * 60 * 1000,
    enabled: true,
  });
}

export function useFighter(id: string) {
  return useQuery<Fighter>({
    queryKey: ['fighters', 'detail', id],
    queryFn: async () => { const { data } = await api.get(fighterEndpoints.detail(id)); return data.data; },
    staleTime: 10 * 60 * 1000,
    enabled: !!id,
  });
}

export function useFighterStats(id: string) {
  return useQuery({
    queryKey: ['fighters', 'stats', id],
    queryFn: async () => { const { data } = await api.get(fighterEndpoints.stats(id)); return data; },
    staleTime: 10 * 60 * 1000,
    enabled: !!id,
  });
}

export function useFightHistory(id: string) {
  return useQuery({
    queryKey: ['fighters', 'history', id],
    queryFn: async () => { const { data } = await api.get(fighterEndpoints.history(id)); return data.data ?? []; },
    staleTime: 30 * 60 * 1000,
    enabled: !!id,
  });
}

export function useSimilarFighters(id: string) {
  return useQuery<Fighter[]>({
    queryKey: ['fighters', 'similar', id],
    queryFn: async () => { const { data } = await api.get(fighterEndpoints.similar(id)); return data.data ?? []; },
    staleTime: 30 * 60 * 1000,
    enabled: !!id,
  });
}

export function useFavoriteFighters() {
  return useQuery<Fighter[]>({
    queryKey: ['fighters', 'favorites'],
    queryFn: async () => { const { data } = await api.get(fighterEndpoints.favorites); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });
}
