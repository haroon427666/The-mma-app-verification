/** Fighters Hooks — composed hooks consuming repository layer */

import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { fightersRepo, statsRepo, historyRepo, similarityRepo, favoritesRepo } from '../repository';
import { fighterKeys, fighterStatsKeys, fighterHistoryKeys, similarityKeys, favoriteKeys } from '../services/queryKeys';
import { fighterCache } from '../services/cache';
import { useFightersStore, useCompareStore, fightersActions, compareActions } from '../store';
import type { FighterProfile, FighterStats, FightHistoryEntry, SimilarFighter } from '../types';

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

// ── useIsFavorite ──
// Derived client-side from the favorites list (/v1/me/favorites) — the backend
// has no per-fighter status endpoint.
export function useIsFavorite(id: string) {
  return useQuery<boolean>({
    queryKey: favoriteKeys.check(id),
    queryFn: async () => {
      try {
        const ids = await favoritesRepo.listFighterIds();
        return ids.includes(id);
      } catch {
        return false;
      }
    },
    staleTime: 60 * 1000,
  });
}

// Re-export store actions
export { fightersActions, compareActions, useCompareStore, useFavoritesStore } from '../store';
