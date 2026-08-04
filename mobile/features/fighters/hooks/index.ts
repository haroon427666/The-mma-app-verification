/** Fighters Hooks — 10 composed hooks consuming repository layer */

import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { fightersRepo, statsRepo, historyRepo, similarityRepo, predictionRepo, recommendationRepo } from '../repository';
import { fighterKeys, fighterStatsKeys, fighterHistoryKeys, similarityKeys, predictionKeys, favoriteKeys } from '../services/queryKeys';
import { fighterCache } from '../services/cache';
import { useFightersStore, useCompareStore, fightersActions, compareActions } from '../store';
import type { FighterProfile, FighterStats, FightHistoryEntry, SimilarFighter, StyleAnalysis, RankHistoryPoint } from '../types';

// ── useFighters ──
export function useFighters() {
  const { filter, sort, selectedWeightClass, searchQuery } = useFightersStore();
  return useInfiniteQuery<FighterProfile[]>({
    queryKey: fighterKeys.list(`${filter}-${sort}-${selectedWeightClass}-${searchQuery}`),
    queryFn: async ({ pageParam = 1 }) => fightersRepo.list({ weightClass: selectedWeightClass ?? undefined, filter: filter === 'all' ? undefined : filter, sort, search: searchQuery || undefined, page: pageParam as number }),
    initialPageParam: 1,
    getNextPageParam: (last, pages) => last.length === 50 ? pages.length + 1 : undefined,
    staleTime: fighterCache.staleTime.list,
  });
}

// ── useFighter ──
export function useFighter(id: string) {
  return useQuery<FighterProfile>({
    queryKey: fighterKeys.detail(id),
    queryFn: () => fightersRepo.getById(id),
    staleTime: fighterCache.staleTime.detail,
    enabled: !!id,
  });
}

// ── useStats ──
export function useStats(id: string) {
  return useQuery<FighterStats>({
    queryKey: fighterStatsKeys.all(id),
    queryFn: () => statsRepo.get(id),
    staleTime: fighterCache.staleTime.stats,
    enabled: !!id,
  });
}

// ── useHistory ──
export function useHistory(id: string, result?: string) {
  return useInfiniteQuery<FightHistoryEntry[]>({
    queryKey: fighterHistoryKeys.list(id, result),
    queryFn: ({ pageParam = 1 }) => historyRepo.list(id, { result, page: pageParam as number }),
    initialPageParam: 1,
    getNextPageParam: (last, pages) => last.length === 20 ? pages.length + 1 : undefined,
    staleTime: fighterCache.staleTime.history,
    enabled: !!id,
  });
}

// ── useSimilarFighters ──
export function useSimilarFighters(id: string) {
  return useQuery<SimilarFighter[]>({
    queryKey: similarityKeys.all(id),
    queryFn: () => similarityRepo.list(id),
    staleTime: fighterCache.staleTime.similar,
    enabled: !!id,
  });
}

// ── useStyleAnalysis ──
export function useStyleAnalysis(id: string) {
  return useQuery<StyleAnalysis>({
    queryKey: [...similarityKeys.all(id), 'style'] as const,
    queryFn: () => similarityRepo.styleAnalysis(id),
    staleTime: fighterCache.staleTime.similar,
    enabled: !!id,
  });
}

// ── usePredictions ──
export function usePredictions(id: string) {
  return useQuery({
    queryKey: predictionKeys.fighter(id),
    queryFn: () => predictionRepo.forFighter(id),
    staleTime: 30 * 60 * 1000,
    enabled: !!id,
  });
}

// ── useIsFavorite ──
export function useIsFavorite(id: string) {
  return useQuery({
    queryKey: favoriteKeys.check(id),
    queryFn: async () => { try { const { data } = await api.get(`/v1/me/favorites/fighters/${id}/status`); return data?.favorited ?? false; } catch { return false; } },
    staleTime: 60 * 1000,
  });
}

// ── useRankHistory ──
export function useRankHistory(id: string) {
  return useQuery<RankHistoryPoint[]>({
    queryKey: [...fighterKeys.detail(id), 'rankhistory'] as const,
    queryFn: async () => { const { data } = await api.get(`/v1/fighters/${id}/rankings/history`); return data?.data ?? []; },
    staleTime: 30 * 60 * 1000,
    enabled: !!id,
  });
}

import api from '@/services/api';

// Re-export store actions
export { fightersActions, compareActions, useCompareStore, useFavoritesStore } from '../store';
