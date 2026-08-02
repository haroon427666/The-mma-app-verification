/** Recommendations — API, Repository, Services, Hooks, Stores, Mutations, Navigation, Screens, Components */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius, shadows } from '@/theme';

// ── Types ──
export interface Recommendation {
  id: string; type: 'fighter' | 'event' | 'fight'; title: string; subtitle: string;
  imageUrl: string | null; score: number; reasons: RecommendationReason[];
}
export interface RecommendationReason { reason: string; weight: number; category: 'social' | 'behavior' | 'similarity' | 'trending' | 'personalized'; }
export interface RecommendationFeedback { recommendationId: string; action: 'liked' | 'dismissed' | 'opened'; }
export type RecView = 'forYou' | 'fighters' | 'events' | 'trending' | 'similar' | 'discover';

// ── API ──
export const recommendationsApi = {
  forYou: (limit = 20) => api.get(`/v1/recommendations?limit=${limit}`),
  fighters: (limit = 10) => api.get(`/v1/recommendations/fighters?limit=${limit}`),
  events: (limit = 10) => api.get(`/v1/recommendations/events?limit=${limit}`),
  trending: () => api.get('/v1/recommendations/trending'),
  discover: () => api.get('/v1/recommendations/discover'),
  becauseWatched: () => api.get('/v1/recommendations/because/watched'),
  becauseFollow: () => api.get('/v1/recommendations/because/follow'),
  feedback: (f: RecommendationFeedback) => api.post('/v1/recommendations/feedback', f),
  profile: () => api.get('/v1/recommendations/profile'),
  dismiss: (id: string) => api.post(`/v1/recommendations/dismiss/${id}`),
};

// ── Repository ──
export const recsRepo = {
  forYou: async (limit = 20) => { const { data } = await recommendationsApi.forYou(limit); return (data?.data ?? data) as Recommendation[]; },
  fighters: async (limit = 10) => { const { data } = await recommendationsApi.fighters(limit); return (data?.data ?? data) as Recommendation[]; },
  events: async (limit = 10) => { const { data } = await recommendationsApi.events(limit); return (data?.data ?? data) as Recommendation[]; },
  trending: async () => { const { data } = await recommendationsApi.trending(); return (data?.data ?? data) as Recommendation[]; },
  discover: async () => { const { data } = await recommendationsApi.discover(); return (data?.data ?? data) as Recommendation[]; },
  becauseWatched: async () => { const { data } = await recommendationsApi.becauseWatched(); return (data?.data ?? data) as Recommendation[]; },
  becauseFollow: async () => { const { data } = await recommendationsApi.becauseFollow(); return (data?.data ?? data) as Recommendation[]; },
  feedback: async (f: RecommendationFeedback) => { await recommendationsApi.feedback(f); },
  profile: async () => { const { data } = await recommendationsApi.profile(); return (data?.data ?? data) as any; },
  dismiss: async (id: string) => { await recommendationsApi.dismiss(id); },
};

// ── Services ──
export const recKeys = {
  all: ['recommendations'] as const,
  forYou: () => [...recKeys.all, 'forYou'] as const,
  fighters: () => [...recKeys.all, 'fighters'] as const,
  events: () => [...recKeys.all, 'events'] as const,
  trending: () => [...recKeys.all, 'trending'] as const,
  discover: () => [...recKeys.all, 'discover'] as const,
  because: (t: string) => [...recKeys.all, 'because', t] as const,
  profile: () => [...recKeys.all, 'profile'] as const,
};
export const recCache = { stale: 5 * 60_000, trendingStale: 2 * 60_000 };

// ── Store ──
export const useRecStore = create<{ view: RecView; dismissedIds: Set<string> }>(() => ({ view: 'forYou', dismissedIds: new Set() }));
export const recActions = {
  setView: (v: RecView) => useRecStore.setState({ view: v }),
  dismiss: (id: string) => useRecStore.setState((s) => { const n = new Set(s.dismissedIds); n.add(id); return { dismissedIds: n }; }),
};

// ── Hooks ──
export function useRecs() { return useQuery<Recommendation[]>({ queryKey: recKeys.forYou(), queryFn: () => recsRepo.forYou(), staleTime: recCache.stale }); }
export function useRecFighters() { return useQuery<Recommendation[]>({ queryKey: recKeys.fighters(), queryFn: () => recsRepo.fighters(), staleTime: recCache.stale }); }
export function useRecEvents() { return useQuery<Recommendation[]>({ queryKey: recKeys.events(), queryFn: () => recsRepo.events(), staleTime: recCache.stale }); }
export function useRecTrending() { return useQuery<Recommendation[]>({ queryKey: recKeys.trending(), queryFn: recsRepo.trending, staleTime: recCache.trendingStale }); }
export function useRecDiscover() { return useQuery<Recommendation[]>({ queryKey: recKeys.discover(), queryFn: recsRepo.discover, staleTime: recCache.trendingStale }); }
export function useRecBecause(type: 'watched' | 'follow') { return useQuery<Recommendation[]>({ queryKey: recKeys.because(type), queryFn: type === 'watched' ? recsRepo.becauseWatched : recsRepo.becauseFollow, staleTime: recCache.stale }); }
export function useRecFeedback() { const qc = useQueryClient(); return useMutation({ mutationFn: (f: RecommendationFeedback) => recsRepo.feedback(f), onSettled: () => qc.invalidateQueries({ queryKey: recKeys.all }) }); }
export function useDismissRec() { const qc = useQueryClient(); return useMutation({ mutationFn: (id: string) => recsRepo.dismiss(id), onMutate: (id) => recActions.dismiss(id), onSettled: () => qc.invalidateQueries({ queryKey: recKeys.all }) }); }

// ── Navigation ──
type RecsStackParamList = { RecsHome: undefined };
const RStack = createNativeStackNavigator<RecsStackParamList>();
export function RecommendationsStack() { return <RStack.Navigator screenOptions={{ headerShown: false }}><RStack.Screen name="RecsHome" component={RecsScreen} /></RStack.Navigator>; }

// ── Screen ──
export function RecsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { view, dismissedIds } = useRecStore();
  const { data: forYou, isLoading, refetch } = useRecs();
  const { data: trending } = useRecTrending();
  const feedback = useRecFeedback();
  const dismiss = useDismissRec();

  const filtered = (forYou ?? []).filter((r) => !dismissedIds.has(r.id));

  return (
    <SafeAreaView style={[rs.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}>
        <Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>For You</Text>

        {filtered.map((rec: Recommendation) => (
          <TouchableOpacity key={rec.id} style={[rs.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={{ flex: 1 }}>
              <Text style={[typography.caption, { color: palette.primary[400], textTransform: 'uppercase', fontWeight: '700' }]}>{rec.type}</Text>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{rec.title}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{rec.subtitle}</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                {rec.reasons?.slice(0, 3).map((r: any, i: number) => (
                  <View key={i} style={[rs.pill, { backgroundColor: palette.surface.elevated }]}>
                    <Text style={[typography.caption, { color: palette.text.secondary }]}>{r.reason}</Text>
                  </View>
                ))}
              </View>
              <View style={rs.feedback}>
                <TouchableOpacity onPress={() => feedback.mutate({ recommendationId: rec.id, action: 'liked' })}><Text style={{ fontSize: 18 }}>👍</Text></TouchableOpacity>
                <TouchableOpacity onPress={() => dismiss.mutate(rec.id)}><Text style={{ fontSize: 18, marginLeft: 16 }}>✕</Text></TouchableOpacity>
              </View>
            </View>
            <View style={[rs.score, { backgroundColor: palette.primary[500] }]}>
              <Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{Math.round(rec.score * 100)}</Text>
            </View>
          </TouchableOpacity>
        ))}

        {filtered.length === 0 && <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', padding: 40 }]}>All caught up!</Text>}

        {trending && (
          <View style={{ padding: spacing.lg }}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.sm }]}>🔥 Trending</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12 }}>
              {trending.slice(0, 6).map((t: any) => (
                <TouchableOpacity key={t.id} style={[rs.trendCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
                  <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]} numberOfLines={2}>{t.title}</Text>
                  <Text style={[typography.caption, { color: palette.primary[400], marginTop: 4 }]}>{t.subtitle}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Theme ──
export const recColors = { forYou: '#3B82F6', similar: '#8B5CF6', trending: '#F97316', discover: '#10B981' } as const;

const rs = StyleSheet.create({
  root: { flex: 1 },
  card: { flexDirection: 'row', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 8, borderRadius: radius.md, borderWidth: 0.5 },
  pill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  feedback: { flexDirection: 'row', marginTop: 8 },
  score: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginLeft: 12 },
  trendCard: { width: 160, padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5 },
});
