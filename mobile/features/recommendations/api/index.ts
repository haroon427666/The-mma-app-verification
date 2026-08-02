/** Recommendations — API, Repository, Services, Stores, Hooks, Mutations */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { Recommendation, RecommendationsDashboard, RecommendationMetrics, RecommendationCategory, RecommendationSort } from '../types';

// ── API ──
export const recommendationsApi = {
  dashboard: () => api.get('/v1/recommendations/dashboard'),
  forYou: (limit = 20) => api.get(`/v1/recommendations?limit=${limit}`),
  fighters: (limit = 10) => api.get(`/v1/recommendations/fighters?limit=${limit}`),
  events: (limit = 5) => api.get(`/v1/recommendations/events?limit=${limit}`),
  becauseYouFollow: () => api.get('/v1/recommendations/because/follow'),
  becauseYouWatched: () => api.get('/v1/recommendations/because/watched'),
  similarFighters: (fighterId: string) => api.get(`/v1/recommendations/fighters/similar?fighter_id=${fighterId}`),
  similarEvents: (eventId: string) => api.get(`/v1/recommendations/events/similar?event_id=${eventId}`),
  trending: (limit = 10) => api.get(`/v1/recommendations/trending?limit=${limit}`),
  hiddenGems: (limit = 5) => api.get(`/v1/recommendations/hidden-gems?limit=${limit}`),
  metrics: () => api.get('/v1/recommendations/metrics'),
  dismiss: (entityId: string) => api.post(`/v1/recommendations/dismiss/${entityId}`),
  feedback: (entityId: string, helpful: boolean) => api.post('/v1/recommendations/feedback', { entity_id: entityId, helpful }),
};

// ── Repository ──
export const recommendationsRepo = {
  dashboard: async () => { const { data } = await recommendationsApi.dashboard(); return (data?.data ?? data) as RecommendationsDashboard; },
  forYou: async (limit = 20) => { const { data } = await recommendationsApi.forYou(limit); return (data?.data ?? data) as Recommendation[]; },
  fighters: async (limit = 10) => { const { data } = await recommendationsApi.fighters(limit); return (data?.data ?? data) as Recommendation[]; },
  events: async (limit = 5) => { const { data } = await recommendationsApi.events(limit); return (data?.data ?? data) as Recommendation[]; },
  becauseYouFollow: async () => { const { data } = await recommendationsApi.becauseYouFollow(); return (data?.data ?? data) as Recommendation[]; },
  becauseYouWatched: async () => { const { data } = await recommendationsApi.becauseYouWatched(); return (data?.data ?? data) as Recommendation[]; },
  trending: async (limit = 10) => { const { data } = await recommendationsApi.trending(limit); return (data?.data ?? data) as Recommendation[]; },
  hiddenGems: async (limit = 5) => { const { data } = await recommendationsApi.hiddenGems(limit); return (data?.data ?? data) as Recommendation[]; },
  similarFighters: async (fighterId: string) => { const { data } = await recommendationsApi.similarFighters(fighterId); return (data?.data ?? data) as Recommendation[]; },
  similarEvents: async (eventId: string) => { const { data } = await recommendationsApi.similarEvents(eventId); return (data?.data ?? data) as Recommendation[]; },
  metrics: async () => { const { data } = await recommendationsApi.metrics(); return (data?.data ?? data) as RecommendationMetrics; },
  dismiss: async (entityId: string) => { await recommendationsApi.dismiss(entityId); },
  feedback: async (entityId: string, helpful: boolean) => { await recommendationsApi.feedback(entityId, helpful); },
};

// ── Services ──
export const recommendationKeys = {
  all: ['recommendations'] as const,
  dashboard: () => [...recommendationKeys.all, 'dashboard'] as const,
  forYou: () => [...recommendationKeys.all, 'forYou'] as const,
  fighters: () => [...recommendationKeys.all, 'fighters'] as const,
  events: () => [...recommendationKeys.all, 'events'] as const,
  because: (type: 'follow' | 'watched') => [...recommendationKeys.all, 'because', type] as const,
  similar: (type: 'fighter' | 'event', id: string) => [...recommendationKeys.all, 'similar', type, id] as const,
  trending: () => [...recommendationKeys.all, 'trending'] as const,
  hiddenGems: () => [...recommendationKeys.all, 'hiddenGems'] as const,
  metrics: () => [...recommendationKeys.all, 'metrics'] as const,
};

export const recommendationCache = { staleTime: 5 * 60_1000, metricsStale: 60 * 60_1000 };

export const recommendationAnalytics = {
  recViewed: (id: string, type: string) => { if (__DEV__) console.log('[analytics] recommendation_viewed', { id, type }); },
  recDismissed: (id: string) => { if (__DEV__) console.log('[analytics] recommendation_dismissed', { id }); },
  recFeedback: (id: string, helpful: boolean) => { if (__DEV__) console.log('[analytics] recommendation_feedback', { id, helpful }); },
  categoryViewed: (cat: string) => { if (__DEV__) console.log('[analytics] rec_category_viewed', { cat }); },
};

// ── Store ──
export const useRecommendationStore = create<{
  category: RecommendationCategory;
  dismissedIds: Set<string>;
}>(() => ({ category: 'for_you', dismissedIds: new Set() }));

export const recommendationActions = {
  setCategory: (c: RecommendationCategory) => useRecommendationStore.setState({ category: c }),
  dismiss: (id: string) => useRecommendationStore.setState((s) => { const n = new Set(s.dismissedIds); n.add(id); return { dismissedIds: n }; }),
};

// ── Hooks ──
export function useRecommendations() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.forYou(), queryFn: () => recommendationsRepo.forYou(), staleTime: recommendationCache.staleTime });
}
export function useRecommendationsDashboard() {
  return useQuery<RecommendationsDashboard>({ queryKey: recommendationKeys.dashboard(), queryFn: recommendationsRepo.dashboard, staleTime: recommendationCache.staleTime });
}
export function useRecommendedFighters() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.fighters(), queryFn: () => recommendationsRepo.fighters(), staleTime: recommendationCache.staleTime });
}
export function useRecommendedEvents() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.events(), queryFn: () => recommendationsRepo.events(), staleTime: recommendationCache.staleTime });
}
export function useBecauseYouFollow() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.because('follow'), queryFn: recommendationsRepo.becauseYouFollow, staleTime: recommendationCache.staleTime });
}
export function useBecauseYouWatched() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.because('watched'), queryFn: recommendationsRepo.becauseYouWatched, staleTime: recommendationCache.staleTime });
}
export function useTrendingRecs() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.trending(), queryFn: () => recommendationsRepo.trending(), staleTime: 2 * 60_1000 });
}
export function useHiddenGems() {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.hiddenGems(), queryFn: () => recommendationsRepo.hiddenGems(), staleTime: recommendationCache.staleTime * 2 });
}
export function useSimilarFightersRec(fighterId: string) {
  return useQuery<Recommendation[]>({ queryKey: recommendationKeys.similar('fighter', fighterId), queryFn: () => recommendationsRepo.similarFighters(fighterId), staleTime: recommendationCache.staleTime, enabled: !!fighterId });
}
export function useRecommendationMetrics() {
  return useQuery<RecommendationMetrics>({ queryKey: recommendationKeys.metrics(), queryFn: recommendationsRepo.metrics, staleTime: recommendationCache.metricsStale });
}

// ── Mutations ──
export function useDismissRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (entityId: string) => recommendationsRepo.dismiss(entityId),
    onMutate: (id) => recommendationActions.dismiss(id),
    onSuccess: (_d, id) => recommendationAnalytics.recDismissed(id),
    onSettled: () => qc.invalidateQueries({ queryKey: ['recommendations'] }),
  });
}
export function useRecommendationFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ entityId, helpful }: { entityId: string; helpful: boolean }) => recommendationsRepo.feedback(entityId, helpful),
    onSuccess: (_d, vars) => recommendationAnalytics.recFeedback(vars.entityId, vars.helpful),
  });
}
