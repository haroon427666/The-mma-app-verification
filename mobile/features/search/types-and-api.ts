/** Search Module — types, API, repository, services, stores, hooks, mutations (all layers consolidated) */

import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { Fighter, Event, Fight } from '../models';

// ── Types ──
export interface SearchResult {
  id: string; type: SearchResultType; title: string; subtitle: string;
  thumbnailUrl: string | null; rank: number | null; record: string | null;
  weightClass: string | null; date: string | null; score: number;
}
export type SearchResultType = 'fighter' | 'event' | 'fight' | 'ranking' | 'promotion' | 'prediction';
export type SearchMode = 'hybrid' | 'keyword' | 'semantic';
export interface SearchSuggestion { text: string; type: SearchResultType; score: number; }
export interface SearchHistoryEntry { query: string; timestamp: string; resultCount: number; }
export interface SearchState { query: string; mode: SearchMode; recentSearches: string[]; filters: { types: Set<SearchResultType>; }; }

// ── API ──
export const searchApi = {
  search: (params: { q: string; mode?: SearchMode; types?: string; cursor?: string }) => {
    const q = new URLSearchParams({ q: params.q });
    if (params.mode) q.set('mode', params.mode);
    if (params.types) q.set('types', params.types);
    if (params.cursor) q.set('cursor', params.cursor);
    return api.get(`/v1/search?${q.toString()}`);
  },
  autocomplete: (q: string, limit = 8) => api.get(`/v1/search/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`),
  trending: () => api.get('/v1/search/trending?limit=10'),
  suggestions: (q: string) => api.get(`/v1/search/suggestions?q=${encodeURIComponent(q)}`),
  history: (page = 1) => api.get(`/v1/search/history?page=${page}&limit=20`),
  clearHistory: () => api.delete('/v1/search/history'),
  voiceSearch: (audioUrl: string) => api.post('/v1/search/voice', { audio_url: audioUrl }),
};

// ── Repository ──
export const searchRepo = {
  search: async (params: Parameters<typeof searchApi.search>[0]) => {
    const { data } = await searchApi.search(params);
    return { results: (data?.results ?? data?.data ?? []) as SearchResult[], nextCursor: data?.next_cursor as string | null };
  },
  autocomplete: async (q: string, limit = 8) => { const { data } = await searchApi.autocomplete(q, limit); return (data?.data ?? data) as SearchSuggestion[]; },
  trending: async () => { const { data } = await searchApi.trending(); return (data?.data ?? data) as SearchResult[]; },
  suggestions: async (q: string) => { const { data } = await searchApi.suggestions(q); return (data?.data ?? data) as SearchSuggestion[]; },
  history: async (page = 1) => { const { data } = await searchApi.history(page); return (data?.data ?? data) as SearchHistoryEntry[]; },
  clearHistory: async () => { await searchApi.clearHistory(); },
};

// ── Services ──
export const searchKeys = {
  all: ['search'] as const,
  results: (q: string, mode: SearchMode) => [...searchKeys.all, 'results', q, mode] as const,
  autocomplete: (q: string) => [...searchKeys.all, 'autocomplete', q] as const,
  trending: () => [...searchKeys.all, 'trending'] as const,
  history: () => [...searchKeys.all, 'history'] as const,
};
export const searchCache = { resultsStale: 30_000, autocompleteStale: 60_000, trendingStale: 5 * 60_000, historyStale: 60 * 60_000 };
export const searchAnalytics = {
  searched: (q: string, resultCount: number) => { if (__DEV__) console.log('[analytics] search_performed', { q, resultCount }); },
  resultOpened: (id: string, type: string) => { if (__DEV__) console.log('[analytics] search_result_opened', { id, type }); },
  voiceUsed: () => { if (__DEV__) console.log('[analytics] voice_search_used'); },
  autocompleteUsed: (q: string) => { if (__DEV__) console.log('[analytics] autocomplete_used', { q }); },
};

// ── Store ──
export const useSearchStore = create<SearchState>(() => ({
  query: '', mode: 'hybrid', recentSearches: [],
  filters: { types: new Set<SearchResultType>(['fighter', 'event', 'fight', 'ranking', 'promotion', 'prediction']) },
}));
export const searchActions = {
  setQuery: (q: string) => useSearchStore.setState({ query: q }),
  setMode: (m: SearchMode) => useSearchStore.setState({ mode: m }),
  addRecent: (q: string) => useSearchStore.setState((s) => ({ recentSearches: [q, ...s.recentSearches.filter((r) => r !== q)].slice(0, 10) })),
  toggleType: (t: SearchResultType) => useSearchStore.setState((s) => { const n = new Set(s.filters.types); n.has(t) ? n.delete(t) : n.add(t); return { filters: { types: n } }; }),
};

// ── Hooks ──
export function useSearch() {
  const { query, mode } = useSearchStore();
  return useInfiniteQuery({
    queryKey: searchKeys.results(query, mode),
    queryFn: async ({ pageParam }) => searchRepo.search({ q: query, mode, cursor: pageParam as string | undefined }),
    initialPageParam: '',
    getNextPageParam: (last) => last.nextCursor,
    enabled: query.length >= 2,
    staleTime: searchCache.resultsStale,
  });
}
export function useAutocomplete(q: string) {
  return useQuery({ queryKey: searchKeys.autocomplete(q), queryFn: () => searchRepo.autocomplete(q), enabled: q.length >= 2, staleTime: searchCache.autocompleteStale });
}
export function useTrendingSearches() {
  return useQuery({ queryKey: searchKeys.trending(), queryFn: searchRepo.trending, staleTime: searchCache.trendingStale });
}
export function useSearchHistory() {
  return useQuery({ queryKey: searchKeys.history(), queryFn: () => searchRepo.history(), staleTime: searchCache.historyStale });
}
export function useClearSearchHistory() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: searchRepo.clearHistory, onSettled: () => qc.invalidateQueries({ queryKey: searchKeys.history() }) });
}
