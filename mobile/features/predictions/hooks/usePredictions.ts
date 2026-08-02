/** Predictions Hooks — composed TanStack Query hooks via repository */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { predictionsRepo } from '../repository';
import { predictionKeys, predictionCache } from '../services/queryKeys';
import { predictionsActions } from '../stores/predictions.store';
import type { FightPrediction, PredictionAccuracyStats, PredictionHistoryEntry, PredictionFactor, MonteCarloResult, PredictionOdds } from '../types';

export function useFightPrediction(fightId: string) {
  return useQuery<FightPrediction>({
    queryKey: predictionKeys.fight(fightId),
    queryFn: () => predictionsRepo.forFight(fightId),
    staleTime: predictionCache.staleTime,
    enabled: !!fightId,
  });
}

export function useEventPredictions(eventId: string) {
  return useQuery<Record<string, FightPrediction>>({
    queryKey: predictionKeys.event(eventId),
    queryFn: () => predictionsRepo.forEvent(eventId),
    staleTime: predictionCache.staleTime,
    enabled: !!eventId,
  });
}

export function usePredictionDashboard() {
  return useQuery({
    queryKey: predictionKeys.dashboard(),
    queryFn: predictionsRepo.dashboard,
    staleTime: predictionCache.staleTime,
  });
}

export function usePredictionHighlights() {
  return useQuery<FightPrediction[]>({
    queryKey: predictionKeys.highlights(),
    queryFn: () => predictionsRepo.highlights(),
    staleTime: predictionCache.staleTime,
  });
}

export function usePredictionHistory(page = 1) {
  return useQuery<PredictionHistoryEntry[]>({
    queryKey: predictionKeys.history(page),
    queryFn: () => predictionsRepo.history(page),
    staleTime: predictionCache.historyStaleTime,
  });
}

export function usePredictionAccuracy() {
  return useQuery<PredictionAccuracyStats>({
    queryKey: predictionKeys.accuracy(),
    queryFn: predictionsRepo.accuracy,
    staleTime: predictionCache.accuracyStaleTime,
  });
}

export function useMatchupPrediction(fAId: string, fBId: string) {
  return useQuery<FightPrediction>({
    queryKey: predictionKeys.matchup(fAId, fBId),
    queryFn: () => predictionsRepo.matchup(fAId, fBId),
    staleTime: predictionCache.staleTime,
    enabled: !!fAId && !!fBId,
  });
}

export function useMonteCarlo(fightId: string) {
  return useQuery<MonteCarloResult>({
    queryKey: predictionKeys.monteCarlo(fightId),
    queryFn: () => predictionsRepo.monteCarlo(fightId),
    staleTime: predictionCache.staleTime,
    enabled: !!fightId,
  });
}

export function usePredictionFactors(fightId: string) {
  return useQuery<PredictionFactor[]>({
    queryKey: predictionKeys.factors(fightId),
    queryFn: () => predictionsRepo.factors(fightId),
    staleTime: predictionCache.staleTime,
    enabled: !!fightId,
  });
}

export function usePredictionOdds(fightId: string) {
  return useQuery<PredictionOdds>({
    queryKey: predictionKeys.odds(fightId),
    queryFn: () => predictionsRepo.odds(fightId),
    staleTime: predictionCache.liveStaleTime,
    enabled: !!fightId,
  });
}

export function useSavedPredictions() {
  return useQuery<FightPrediction[]>({
    queryKey: predictionKeys.saved(),
    queryFn: predictionsRepo.saved,
    staleTime: 60 * 1000,
  });
}

export function useSavePrediction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fightId: string) => predictionsRepo.save(fightId),
    onMutate: (id) => predictionsActions.addSaved(id),
    onSettled: () => qc.invalidateQueries({ queryKey: predictionKeys.saved() }),
  });
}

export function useUnsavePrediction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fightId: string) => predictionsRepo.unsave(fightId),
    onMutate: (id) => predictionsActions.removeSaved(id),
    onSettled: () => qc.invalidateQueries({ queryKey: predictionKeys.saved() }),
  });
}

export function useSharePrediction() {
  return useMutation({
    mutationFn: (fightId: string) => predictionsRepo.share(fightId),
  });
}
