/** Search module — hybrid search with autocomplete, history, voice hooks, popularity */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';

// ── Types ──
export interface SearchResult { id: string; type: 'fighter' | 'event' | 'fight' | 'promotion' | 'venue'; name: string; fullName?: string; subtitle?: string; record?: string; imageUrl?: string | null; weightClass?: string | null; score: number; }
export interface SearchState { query: string; recentSearches: string[]; isSearching: boolean; showResults: boolean; }

// ── API ──
export const searchApi = {
  query: (q: string, type?: string) => api.get(`/v1/search?q=${encodeURIComponent(q)}${type ? `&type=${type}` : ''}`),
  autocomplete: (q: string) => api.get(`/v1/search/autocomplete?q=${encodeURIComponent(q)}`),
  popular: () => api.get('/v1/search/popular'),
};

// ── Repository ──
export const searchRepo = {
  query: async (q: string, type?: string) => { const { data } = await searchApi.query(q, type); return (data?.results ?? data) as SearchResult[]; },
  autocomplete: async (q: string) => { const { data } = await searchApi.autocomplete(q); return (data?.data ?? data) as string[]; },
  popular: async () => { const { data } = await searchApi.popular(); return (data?.data ?? data) as string[]; },
};

// ── Services ──
export const searchKeys = { all: ['search'] as const, query: (q: string) => [...searchKeys.all, 'query', q] as const, autocomplete: (q: string) => [...searchKeys.all, 'autocomplete', q] as const, popular: () => [...searchKeys.all, 'popular'] as const };
export const searchAnalytics = { searchPerformed: (q: string, count: number) => { if (__DEV__) console.log('[analytics] search', { q, count }); } };

// ── Store ──
export const useSearchStore = create<SearchState>(() => ({ query: '', recentSearches: [], isSearching: false, showResults: false }));
export const searchActions = {
  setQuery: (q: string) => useSearchStore.setState({ query: q, showResults: false }),
  addRecent: (q: string) => useSearchStore.setState((s) => ({ recentSearches: [q, ...s.recentSearches.filter((r) => r !== q)].slice(0, 10) })),
  setSearching: (v: boolean) => useSearchStore.setState({ isSearching: v }),
  showResults: () => useSearchStore.setState({ showResults: true }),
  clear: () => useSearchStore.setState({ query: '', isSearching: false, showResults: false }),
};

// ── Hooks ──
export function useSearch(query: string) {
  const result = useQuery<SearchResult[]>({ queryKey: searchKeys.query(query), queryFn: () => searchRepo.query(query), enabled: query.length >= 2, staleTime: 60_1000 });
  return { ...result, performSearch: () => { if (result.data) searchAnalytics.searchPerformed(query, result.data.length); } };
}
export function useAutocomplete(query: string) {
  return useQuery<string[]>({ queryKey: searchKeys.autocomplete(query), queryFn: () => searchRepo.autocomplete(query), enabled: query.length >= 2, staleTime: 30_1000 });
}
export function usePopularSearches() {
  return useQuery<string[]>({ queryKey: searchKeys.popular(), queryFn: searchRepo.popular, staleTime: 60 * 60_1000 });
}

// ── Screen ──
import React, { useCallback } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { typography, spacing, radius } from '@/theme';

export function SearchScreen({ navigation }: any) {
  const { query, showResults, recentSearches } = useSearchStore();
  const { data: results } = useSearch(query);
  const { data: popular } = usePopularSearches();
  const { data: suggestions } = useAutocomplete(query);

  const handleSubmit = useCallback(() => {
    if (query.trim().length >= 2) {
      searchActions.addRecent(query.trim());
      searchActions.showResults();
      searchAnalytics.searchPerformed(query.trim(), results?.length ?? 0);
    }
  }, [query, results]);

  return (
    <SafeAreaView style={[st.root, { backgroundColor: '#0A0A0A' }]}>
      <View style={[st.bar, { backgroundColor: '#1A1A2E', borderColor: '#2A2A3E' }]}>
        <Text style={st.searchIcon}>🔍</Text>
        <TextInput style={[st.input, { color: '#FFF' }]} placeholder="Search fighters, events, fights..." placeholderTextColor="#6B7280"
          value={query} onChangeText={searchActions.setQuery} onSubmitEditing={handleSubmit} returnKeyType="search" autoFocus />
        {query ? <TouchableOpacity onPress={searchActions.clear}><Text style={{ color: '#6B7280', fontSize: 18 }}>✕</Text></TouchableOpacity> : null}
      </View>

      {!showResults && !query && (
        <View style={{ padding: spacing.lg }}>
          {recentSearches.length > 0 && (
            <View style={{ marginBottom: spacing.xl }}>
              <Text style={[typography.bodySmall, { color: '#6B7280', marginBottom: 8 }]}>Recent</Text>
              {recentSearches.map((s, i) => (
                <TouchableOpacity key={i} onPress={() => { searchActions.setQuery(s); searchActions.showResults(); }}
                  style={st.suggestionRow}><Text style={[typography.body, { color: '#9CA3AF' }]}>{s}</Text></TouchableOpacity>
              ))}
            </View>
          )}
          <Text style={[typography.bodySmall, { color: '#6B7280', marginBottom: 8 }]}>Popular Searches</Text>
          {(popular ?? ['Islam Makhachev', 'Jon Jones', 'UFC', 'Lightweight rankings', 'Alex Pereira']).map((s, i) => (
            <TouchableOpacity key={i} onPress={() => { searchActions.setQuery(s); searchActions.showResults(); }}
              style={st.suggestionRow}><Text style={[typography.body, { color: '#9CA3AF' }]}>{s}</Text></TouchableOpacity>
          ))}
        </View>
      )}

      {showResults && (
        <FlatList
          data={results ?? []}
          keyExtractor={(r: SearchResult) => r.id}
          renderItem={({ item }) => (
            <TouchableOpacity style={st.resultRow} onPress={() => navigation.navigate(item.type === 'fighter' ? 'fighterDetail' : 'eventDetail', { id: item.id })}>
              <Text style={[typography.bodySmall, { color: '#3B82F6', textTransform: 'uppercase' }]}>{item.type}</Text>
              <Text style={[typography.body, { color: '#FFF', fontWeight: '600' }]}>{item.name || item.fullName}</Text>
              {item.subtitle && <Text style={[typography.caption, { color: '#6B7280' }]}>{item.subtitle}</Text>}
            </TouchableOpacity>
          )}
          ListEmptyComponent={query.length >= 2 ? <Text style={[typography.body, { color: '#6B7280', textAlign: 'center', marginTop: 60 }]}>No results for "{query}"</Text> : null}
        />
      )}
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  bar: { flexDirection: 'row', alignItems: 'center', margin: spacing.lg, paddingHorizontal: 14, borderRadius: radius.md, borderWidth: 1, height: 48 },
  searchIcon: { fontSize: 16, marginRight: 8 },
  input: { flex: 1, fontSize: 16 },
  suggestionRow: { paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  resultRow: { padding: spacing.md, marginHorizontal: spacing.lg, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
});
