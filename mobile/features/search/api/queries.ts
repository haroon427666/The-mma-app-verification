/** Search API + store */

import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';

interface SearchResult { id: string; type: 'fighter' | 'event' | 'fight'; name: string; record?: string; }

export function useSearch(query: string) {
  return useQuery<SearchResult[]>({
    queryKey: ['search', query],
    queryFn: async () => {
      if (query.length < 2) return [];
      const { data } = await api.get(`/v1/search?q=${encodeURIComponent(query)}`);
      return data.results ?? [];
    },
    enabled: query.length >= 2,
    staleTime: 60 * 1000,
  });
}

interface SearchState {
  query: string;
  recentSearches: string[];
  isSearching: boolean;
}

export const useSearchStore = create<SearchState>(() => ({ query: '', recentSearches: [], isSearching: false }));
export const searchActions = {
  setQuery: (q: string) => useSearchStore.setState({ query: q }),
  addRecent: (q: string) => useSearchStore.setState((s) => ({
    recentSearches: [q, ...s.recentSearches.filter((r) => r !== q)].slice(0, 10),
  })),
  setSearching: (v: boolean) => useSearchStore.setState({ isSearching: v }),
};
