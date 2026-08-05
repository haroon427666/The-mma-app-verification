/** Rankings Hooks — consuming repository */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rankingsRepo } from '../repository';
import { rankingKeys, rankingCache, rankingAnalytics } from '../services';
import type { P4PRanking, Division, GOATEntry, ProspectEntry, RankingMovement, FighterStreak } from '../types';

export function useP4P() {
  const result = useQuery<P4PRanking[]>({ queryKey: rankingKeys.p4p(), queryFn: rankingsRepo.p4p, staleTime: rankingCache.staleTime });
  return { ...result, onMount: rankingAnalytics.p4pViewed };
}

export function useDivisionRankings(division: string) {
  return useQuery<Division>({ queryKey: rankingKeys.division(division), queryFn: () => rankingsRepo.byDivision(division), staleTime: rankingCache.staleTime, enabled: !!division });
}

export function useGOAT() {
  return useQuery<GOATEntry[]>({ queryKey: rankingKeys.goat(), queryFn: rankingsRepo.goat, staleTime: rankingCache.staleTime * 2 });
}

export function useProspects(division?: string) {
  return useQuery<ProspectEntry[]>({ queryKey: rankingKeys.prospects(division), queryFn: () => rankingsRepo.prospects(division), staleTime: rankingCache.staleTime });
}

export function useRankingMovement(division?: string) {
  return useQuery<RankingMovement[]>({ queryKey: rankingKeys.movement(), queryFn: () => rankingsRepo.movement({ division }), staleTime: rankingCache.liveStaleTime });
}

export function useStreaks() {
  return useQuery<FighterStreak[]>({ queryKey: rankingKeys.streaks(), queryFn: rankingsRepo.streaks, staleTime: rankingCache.staleTime });
}

export function useChampions() {
  return useQuery({ queryKey: rankingKeys.champions(), queryFn: rankingsRepo.champions, staleTime: rankingCache.staleTime * 2 });
}

export function useTitleDefenses() {
  return useQuery({ queryKey: rankingKeys.titleDefenses(), queryFn: rankingsRepo.titleDefenses, staleTime: rankingCache.staleTime * 2 });
}

// Mutations
export function useFavoriteRanking() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => api.post(`/v1/me/favorites/fighters/${id}`), onSettled: () => qc.invalidateQueries({ queryKey: ['favorites'] }) });
}

import api from '@/services/api';
