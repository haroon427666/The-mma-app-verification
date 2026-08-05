/** Predictions — API, Repository, Services, Stores, Hooks, Mutations (all layers) */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { FightPrediction, PredictionDashboard, PredictionHistoryEntry, PredictionAccuracyStats, PredictionView, PredictionSort } from '../types';

// ── API ──
export const predictionsApi = {
  forFight: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}`),
  forEvent: (eventId: string) => api.get(`/v1/predictions/event/${eventId}`),
  dashboard: () => api.get('/v1/predictions/dashboard'),
  highlights: () => api.get('/v1/predictions/highlights?limit=8'),
  history: (params?: { page?: number; limit?: number }) => {
    const q = new URLSearchParams(); if (params?.page) q.set('page', String(params.page)); if (params?.limit) q.set('limit', String(params.limit ?? 20));
    return api.get(`/v1/predictions/history?${q.toString()}`);
  },
  accuracy: () => api.get('/v1/predictions/accuracy'),
  matchup: (fighterAId: string, fighterBId: string) => api.get(`/v1/predictions/matchup?fighter_a=${fighterAId}&fighter_b=${fighterBId}`),
  save: (fightId: string) => api.post(`/v1/predictions/saved/${fightId}`),
  unsave: (fightId: string) => api.delete(`/v1/predictions/saved/${fightId}`),
  saved: () => api.get('/v1/predictions/saved'),
};

// ── Repository ──
export const predictionsRepo = {
  forFight: async (fightId: string) => { const { data } = await predictionsApi.forFight(fightId); return data as FightPrediction; },
  forEvent: async (eventId: string) => { const { data } = await predictionsApi.forEvent(eventId); return (data ?? {}) as Record<string, FightPrediction>; },
  dashboard: async () => { const { data } = await predictionsApi.dashboard(); return (data?.data ?? data) as PredictionDashboard; },
  highlights: async () => { const { data } = await predictionsApi.highlights(); return (data?.data ?? data) as FightPrediction[]; },
  history: async (params?: { page?: number; limit?: number }) => { const { data } = await predictionsApi.history(params); return (data?.data ?? data) as PredictionHistoryEntry[]; },
  accuracy: async () => { const { data } = await predictionsApi.accuracy(); return (data?.data ?? data) as PredictionAccuracyStats; },
  matchup: async (a: string, b: string) => { const { data } = await predictionsApi.matchup(a, b); return data as FightPrediction; },
  save: async (fightId: string) => { await predictionsApi.save(fightId); },
  unsave: async (fightId: string) => { await predictionsApi.unsave(fightId); },
  saved: async () => { const { data } = await predictionsApi.saved(); return (data?.data ?? data) as FightPrediction[]; },
};

// ── Services ──
export const predictionKeys = {
  all: ['predictions'] as const,
  fight: (fightId: string) => [...predictionKeys.all, 'fight', fightId] as const,
  event: (eventId: string) => [...predictionKeys.all, 'event', eventId] as const,
  dashboard: () => [...predictionKeys.all, 'dashboard'] as const,
  highlights: () => [...predictionKeys.all, 'highlights'] as const,
  history: () => [...predictionKeys.all, 'history'] as const,
  accuracy: () => [...predictionKeys.all, 'accuracy'] as const,
  matchup: (a: string, b: string) => [...predictionKeys.all, 'matchup', a, b] as const,
  saved: () => [...predictionKeys.all, 'saved'] as const,
};

export const predictionCache = { staleTime: 5 * 60_1000, historyStale: 60 * 60_1000, liveStale: 30_1000 };

export const predictionAnalytics = {
  predictionViewed: (fightId: string) => { if (__DEV__) console.log('[analytics] prediction_viewed', { fightId }); },
  monteCarloRan: (fightId: string) => { if (__DEV__) console.log('[analytics] monte_carlo_ran', { fightId }); },
  predictionSaved: (fightId: string) => { if (__DEV__) console.log('[analytics] prediction_saved', { fightId }); },
  predictionShared: (fightId: string) => { if (__DEV__) console.log('[analytics] prediction_shared', { fightId }); },
  accuracyViewed: () => { if (__DEV__) console.log('[analytics] prediction_accuracy_viewed'); },
};

export const predictionDeeplinks = { fight: (id: string) => `mma://prediction/${id}`, compare: (a: string, b: string) => `mma://prediction/compare/${a}/${b}` };

// ── Store ──
export const usePredictionStore = create<{ view: PredictionView; sortBy: PredictionSort; savedIds: Set<string> }>(() => ({
  view: 'dashboard', sortBy: 'confidence', savedIds: new Set(),
}));
export const predictionActions = {
  setView: (v: PredictionView) => usePredictionStore.setState({ view: v }),
  setSort: (s: PredictionSort) => usePredictionStore.setState({ sortBy: s }),
  addSaved: (id: string) => usePredictionStore.setState((s) => { const n = new Set(s.savedIds); n.add(id); return { savedIds: n }; }),
  removeSaved: (id: string) => usePredictionStore.setState((s) => { const n = new Set(s.savedIds); n.delete(id); return { savedIds: n }; }),
};

// ── Hooks ──
export function useFightPrediction(fightId: string) {
  return useQuery<FightPrediction>({ queryKey: predictionKeys.fight(fightId), queryFn: () => predictionsRepo.forFight(fightId), staleTime: predictionCache.staleTime, enabled: !!fightId });
}
export function useEventPredictions(eventId: string) {
  return useQuery<Record<string, FightPrediction>>({ queryKey: predictionKeys.event(eventId), queryFn: () => predictionsRepo.forEvent(eventId), staleTime: predictionCache.staleTime, enabled: !!eventId });
}
export function usePredictionDashboard() {
  return useQuery<PredictionDashboard>({ queryKey: predictionKeys.dashboard(), queryFn: predictionsRepo.dashboard, staleTime: predictionCache.staleTime });
}
export function usePredictionHighlights() {
  return useQuery<FightPrediction[]>({ queryKey: predictionKeys.highlights(), queryFn: predictionsRepo.highlights, staleTime: predictionCache.staleTime });
}
export function usePredictionHistory(page = 1) {
  return useQuery<PredictionHistoryEntry[]>({ queryKey: [...predictionKeys.history(), page], queryFn: () => predictionsRepo.history({ page }), staleTime: predictionCache.historyStale });
}
export function usePredictionAccuracy() {
  return useQuery<PredictionAccuracyStats>({ queryKey: predictionKeys.accuracy(), queryFn: predictionsRepo.accuracy, staleTime: predictionCache.historyStale });
}
export function useMatchupPrediction(a: string, b: string) {
  return useQuery<FightPrediction>({ queryKey: predictionKeys.matchup(a, b), queryFn: () => predictionsRepo.matchup(a, b), staleTime: predictionCache.staleTime, enabled: !!a && !!b });
}
export function useSavedPredictions() {
  return useQuery<FightPrediction[]>({ queryKey: predictionKeys.saved(), queryFn: predictionsRepo.saved, staleTime: 60_1000 });
}

// ── Mutations ──
export function useSavePrediction() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (fightId: string) => predictionsRepo.save(fightId), onMutate: (id) => predictionActions.addSaved(id), onSuccess: (_d, id) => predictionAnalytics.predictionSaved(id), onSettled: () => qc.invalidateQueries({ queryKey: ['predictions', 'saved'] }) });
}
export function useUnsavePrediction() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (fightId: string) => predictionsRepo.unsave(fightId), onMutate: (id) => predictionActions.removeSaved(id), onSettled: () => qc.invalidateQueries({ queryKey: ['predictions', 'saved'] }) });
}
