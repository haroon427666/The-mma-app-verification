/** Search Module — types, API, repo, hooks, store, nav, screen, components, theme */

import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import React, { useCallback, useRef, useState } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity, ScrollView, StyleSheet, ActivityIndicator, Keyboard } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';

// ── Types ──
export interface SearchResult { id: string; type: 'fighter' | 'event' | 'fight' | 'ranking' | 'promotion' | 'prediction'; title: string; subtitle: string; imageUrl: string | null; score: number; }
export type SearchMode = 'hybrid' | 'keyword' | 'semantic';

// ── API ──
export const searchApi = {
  search: (params: { q: string; mode?: SearchMode; types?: string; cursor?: string }) => {
    const q = new URLSearchParams({ q: params.q }); if (params.mode) q.set('mode', params.mode); if (params.types) q.set('types', params.types); if (params.cursor) q.set('cursor', params.cursor);
    return api.get(`/v1/search?${q.toString()}`);
  },
  autocomplete: (q: string) => api.get(`/v1/search/autocomplete?q=${encodeURIComponent(q)}`),
  trending: () => api.get('/v1/search/trending?limit=10'),
  popular: () => api.get('/v1/search/popular'),
  history: () => api.get('/v1/search/history?limit=20'),
  clearHistory: () => api.delete('/v1/search/history'),
};

// ── Repository ──
export const searchRepo = {
  search: async (p: Parameters<typeof searchApi.search>[0]) => { const { data } = await searchApi.search(p); return { results: (data?.results ?? data?.data ?? []) as SearchResult[], nextCursor: data?.next_cursor as string | null }; },
  autocomplete: async (q: string) => { const { data } = await searchApi.autocomplete(q); return (data?.data ?? data) as string[]; },
  trending: async () => { const { data } = await searchApi.trending(); return (data?.data ?? data) as SearchResult[]; },
  popular: async () => { const { data } = await searchApi.popular(); return (data?.data ?? data) as string[]; },
  history: async () => { const { data } = await searchApi.history(); return (data?.data ?? data) as string[]; },
  clearHistory: async () => { await searchApi.clearHistory(); },
};

// ── Services ──
export const searchKeys = {
  all: ['search'] as const,
  results: (q: string) => [...searchKeys.all, 'results', q] as const,
  autocomplete: (q: string) => [...searchKeys.all, 'autocomplete', q] as const,
  trending: () => [...searchKeys.all, 'trending'] as const,
  popular: () => [...searchKeys.all, 'popular'] as const,
  history: () => [...searchKeys.all, 'history'] as const,
};

// ── Store ──
export const useSearchStore = create<{ query: string; mode: SearchMode; recent: string[] }>(() => ({ query: '', mode: 'hybrid', recent: [] }));
export const searchActions = {
  setQuery: (q: string) => useSearchStore.setState({ query: q }),
  addRecent: (q: string) => useSearchStore.setState((s) => ({ recent: [q, ...s.recent.filter((r) => r !== q)].slice(0, 10) })),
};

// ── Hooks ──
export function useSearch() {
  const { query, mode } = useSearchStore();
  return useInfiniteQuery({
    queryKey: searchKeys.results(query), queryFn: ({ pageParam }) => searchRepo.search({ q: query, mode, cursor: pageParam as string | undefined }),
    initialPageParam: undefined, getNextPageParam: (last) => last.nextCursor, enabled: query.length >= 2, staleTime: 30_000,
  });
}
export function useAutocomplete(q: string) { return useQuery({ queryKey: searchKeys.autocomplete(q), queryFn: () => searchRepo.autocomplete(q), enabled: q.length >= 2 }); }
export function useTrendingSearches() { return useQuery({ queryKey: searchKeys.trending(), queryFn: searchRepo.trending }); }
export function usePopularSearches() { return useQuery({ queryKey: searchKeys.popular(), queryFn: searchRepo.popular }); }
export function useSearchHistory() { return useQuery({ queryKey: searchKeys.history(), queryFn: searchRepo.history }); }
export function useClearHistory() { const qc = useQueryClient(); return useMutation({ mutationFn: searchRepo.clearHistory, onSettled: () => qc.invalidateQueries({ queryKey: searchKeys.history() }) }); }

// ── Navigation ──
const SStack = createNativeStackNavigator();
export function SearchStack() { return <SStack.Navigator screenOptions={{ headerShown: false }}><SStack.Screen name="Search" component={SearchScreen} /></SStack.Navigator>; }

// ── Screen ──
export function SearchScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { query, recent } = useSearchStore();
  const [showResults, setShowResults] = useState(false);
  const { data: autoData } = useAutocomplete(query);
  const { data: searchData, fetchNextPage, isLoading } = useSearch();
  const { data: popular } = usePopularSearches();
  const results = searchData?.pages.flatMap((p: any) => p.results ?? []) ?? [];

  const handleSearch = useCallback((q: string) => { if (q.length >= 2) { searchActions.addRecent(q); setShowResults(true); Keyboard.dismiss(); } }, []);

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[st.bar, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
        <Text style={{ fontSize: 16, marginRight: 8 }}>🔍</Text>
        <TextInput style={[st.input, { color: palette.text.primary }]} placeholder="Search fighters, events..." placeholderTextColor={palette.text.tertiary}
          value={query} onChangeText={searchActions.setQuery} onSubmitEditing={() => handleSearch(query)} returnKeyType="search" />
        {query ? <TouchableOpacity onPress={() => { searchActions.setQuery(''); setShowResults(false); }}><Text style={{ color: palette.text.tertiary, fontSize: 20 }}>✕</Text></TouchableOpacity> : null}
      </View>

      {!showResults && query.length >= 2 && (autoData ?? []).length > 0 && (
        <View style={[st.dropdown, { backgroundColor: '#1A1A2E' }]}>
          {autoData.slice(0, 6).map((s: any, i: number) => (
            <TouchableOpacity key={i} onPress={() => { searchActions.setQuery(s); handleSearch(s); }} style={[st.sugRow, { borderColor: palette.surface.border }]}>
              <Text style={[typography.caption, { color: palette.primary[400] }]}>{typeof s === 'string' ? s : s.text}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {!showResults && query.length < 2 && (
        <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
          {recent.length > 0 && (
            <View style={{ marginBottom: spacing.xl }}>
              <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase', marginBottom: 8 }]}>Recent</Text>
              {recent.slice(0, 5).map((r: string, i: number) => (
                <TouchableOpacity key={i} onPress={() => { searchActions.setQuery(r); handleSearch(r); }} style={st.recentRow}>
                  <Text style={[typography.body, { color: palette.text.primary }]}>{r}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
          {popular && (
            <View>
              <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase', marginBottom: 12 }]}>Popular</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                {popular.slice(0, 8).map((s: string, i: number) => (
                  <TouchableOpacity key={i} onPress={() => { searchActions.setQuery(s); handleSearch(s); }} style={[st.popPill, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
                    <Text style={[typography.caption, { color: palette.text.secondary }]}>{s}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}
        </ScrollView>
      )}

      {showResults && (
        <FlatList data={results as SearchResult[]} keyExtractor={(r) => r.id} onEndReached={() => fetchNextPage()}
          renderItem={({ item }) => (
            <TouchableOpacity style={[st.result, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={[st.typeBadge, { backgroundColor: typeColor(item.type) }]}><Text style={{ color: '#FFF', fontSize: 9, fontWeight: '700', textTransform: 'uppercase' }}>{item.type}</Text></View>
                  {item.score > 0 && <Text style={[typography.caption, { color: palette.text.tertiary }]}>{Math.round(item.score * 100)}%</Text>}
                </View>
                <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600', marginTop: 4 }]}>{item.title}</Text>
                <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.subtitle}</Text>
              </View>
            </TouchableOpacity>
          )}
          ListEmptyComponent={!isLoading ? <Text style={{ color: '#9CA3AF', textAlign: 'center', marginTop: 60 }}>No results for "{query}"</Text> : <ActivityIndicator style={{ marginTop: 40 }} />}
        />
      )}
    </SafeAreaView>
  );
}

function typeColor(type: string): string { const m: Record<string, string> = { fighter: '#3B82F6', event: '#8B5CF6', fight: '#EF4444', ranking: '#F59E0B', promotion: '#10B981', prediction: '#F97316' }; return m[type] ?? '#6B7280'; }

// ── Theme ──
export const searchColors = { types: { fighter: '#3B82F6', event: '#8B5CF6', fight: '#EF4444', ranking: '#F59E0B', promotion: '#10B981', prediction: '#F97316' } } as const;

const st = StyleSheet.create({
  root: { flex: 1 },
  bar: { flexDirection: 'row', alignItems: 'center', margin: spacing.lg, paddingHorizontal: 14, borderWidth: 1, borderRadius: radius.md, height: 48 },
  input: { flex: 1, fontSize: 16 },
  dropdown: { marginHorizontal: spacing.lg, borderRadius: radius.md, overflow: 'hidden', marginTop: -8 },
  sugRow: { padding: 14, borderBottomWidth: 0.5 },
  recentRow: { paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  popPill: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 18, borderWidth: 0.5 },
  result: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5 },
  typeBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
});
