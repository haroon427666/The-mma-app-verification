/** Rankings Hooks — 10+ hooks consuming repository */

import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rankingsRepo } from '../repository';
import { rankingKeys, rankingCache, rankingAnalytics } from '../services';
import { useRankingsStore } from '../stores';
import type { P4PRanking, Division, RankingHistoryPoint, GOATEntry, ProspectEntry, RankingMovement, FighterStreak, ChampionRecord, RankingFighter } from '../types';

export function useP4P() {
  const result = useQuery<P4PRanking[]>({ queryKey: rankingKeys.p4p(), queryFn: rankingsRepo.p4p, staleTime: rankingCache.staleTime });
  return { ...result, onMount: rankingAnalytics.p4pViewed };
}

export function useDivisionRankings(division: string) {
  return useQuery<Division>({ queryKey: rankingKeys.division(division), queryFn: () => rankingsRepo.byDivision(division), staleTime: rankingCache.staleTime, enabled: !!division });
}

export function useRankingHistory(fighterId: string) {
  return useQuery<RankingHistoryPoint[]>({ queryKey: rankingKeys.history(fighterId), queryFn: () => rankingsRepo.history(fighterId), staleTime: rankingCache.staleTime, enabled: !!fighterId });
}

export function useGOAT() {
  return useQuery<GOATEntry[]>({ queryKey: rankingKeys.goat(), queryFn: rankingsRepo.goat, staleTime: rankingCache.staleTime * 2 });
}

export function useProspects(division?: string) {
  return useQuery<ProspectEntry[]>({ queryKey: rankingKeys.prospects(division), queryFn: () => rankingsRepo.prospects(division), staleTime: rankingCache.staleTime });
}

export function useRankingMovement(direction?: string) {
  return useQuery<RankingMovement[]>({ queryKey: rankingKeys.movement(), queryFn: () => rankingsRepo.movement({ direction }), staleTime: rankingCache.liveStaleTime });
}

export function useStreaks() {
  return useQuery<FighterStreak[]>({ queryKey: rankingKeys.streaks(), queryFn: rankingsRepo.streaks, staleTime: rankingCache.staleTime });
}

export function useChampions() {
  return useQuery({ queryKey: rankingKeys.champions(), queryFn: rankingsRepo.champions, staleTime: rankingCache.staleTime * 2 });
}

export function useChampionsHistory(weightClass?: string) {
  return useQuery<ChampionRecord[]>({ queryKey: rankingKeys.championsHistory(weightClass), queryFn: () => rankingsRepo.championsHistory(weightClass), staleTime: rankingCache.staleTime * 2 });
}

export function useTitleDefenses() {
  return useQuery({ queryKey: rankingKeys.titleDefenses(), queryFn: rankingsRepo.titleDefenses, staleTime: rankingCache.staleTime * 2 });
}

export function useEloRankings(weightClass?: string) {
  return useQuery({ queryKey: rankingKeys.elo(), queryFn: () => rankingsRepo.elo({ weightClass }), staleTime: rankingCache.staleTime });
}

export function useCompositeRankings(weightClass?: string) {
  return useQuery({ queryKey: rankingKeys.composite(), queryFn: () => rankingsRepo.composite({ weightClass }), staleTime: rankingCache.staleTime });
}

// Mutations
export function useFavoriteRanking() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => api.post(`/v1/favorites/fighters/${id}`), onSettled: () => qc.invalidateQueries({ queryKey: ['favorites'] }) });
}

import api from '@/services/api';
