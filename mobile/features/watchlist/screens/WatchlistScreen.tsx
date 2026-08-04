/** Watchlist module — tracked fighters + events with optimistic remove */

import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import { typography, spacing, radius } from '@/theme';

// ── Types ──
export interface WatchlistEvent { id: string; name: string; date: string; venue?: string; fightCount?: number; status?: string; }
export interface FavoriteFighter { id: string; fullName?: string; lastName?: string; record?: string; rank?: number; weightClass?: string; }

// ── API + Repository ──
export const watchlistApi = {
  events: () => api.get('/v1/me/watchlist/events'),
  addEvent: (id: string) => api.post(`/v1/me/watchlist/events/${id}`),
  removeEvent: (id: string) => api.delete(`/v1/me/watchlist/events/${id}`),
  fighters: () => api.get('/v1/me/favorites/fighters'),
  removeFighter: (id: string) => api.delete(`/v1/me/favorites/fighters/${id}`),
};
export const watchlistRepo = {
  events: async () => { const { data } = await watchlistApi.events(); return (data?.data ?? data) as WatchlistEvent[]; },
  addEvent: async (id: string) => { await watchlistApi.addEvent(id); },
  removeEvent: async (id: string) => { await watchlistApi.removeEvent(id); },
  fighters: async () => { const { data } = await watchlistApi.fighters(); return (data?.data ?? data) as FavoriteFighter[]; },
  removeFighter: async (id: string) => { await watchlistApi.removeFighter(id); },
};

// ── Services ──
export const watchlistKeys = {
  all: ['watchlist'] as const,
  events: () => [...watchlistKeys.all, 'events'] as const,
  fighters: () => [...watchlistKeys.all, 'fighters'] as const,
};

// ── Store ──
export const useWatchlistStore = create<{ tab: 'events' | 'fighters' }>(() => ({ tab: 'events' }));

// ── Hooks + Mutations ──
export function useWatchlist() {
  return useQuery({
    queryKey: watchlistKeys.all, queryFn: async () => {
      const [events, fighters] = await Promise.all([watchlistRepo.events(), watchlistRepo.fighters()]);
      return { events, fighters };
    }, staleTime: 5 * 60_1000,
  });
}
export function useRemoveEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => watchlistRepo.removeEvent(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: watchlistKeys.events() });
      const prev = qc.getQueryData<{ events: WatchlistEvent[]; fighters: FavoriteFighter[] }>(watchlistKeys.all);
      qc.setQueryData(watchlistKeys.all, (old: any) => old ? { ...old, events: old.events.filter((e: WatchlistEvent) => e.id !== id) } : old);
      return { prev };
    },
    onError: (_err, _id, ctx) => { if (ctx?.prev) qc.setQueryData(watchlistKeys.all, ctx.prev); },
    onSettled: () => qc.invalidateQueries({ queryKey: watchlistKeys.all }),
  });
}
export function useRemoveFighter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => watchlistRepo.removeFighter(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: watchlistKeys.fighters() });
      const prev = qc.getQueryData<{ events: WatchlistEvent[]; fighters: FavoriteFighter[] }>(watchlistKeys.all);
      qc.setQueryData(watchlistKeys.all, (old: any) => old ? { ...old, fighters: old.fighters.filter((f: FavoriteFighter) => f.id !== id) } : old);
      return { prev };
    },
    onError: (_err, _id, ctx) => { if (ctx?.prev) qc.setQueryData(watchlistKeys.all, ctx.prev); },
    onSettled: () => qc.invalidateQueries({ queryKey: watchlistKeys.all }),
  });
}

// ── Screen ──
import { useTheme } from '@/hooks/useTheme';

export function WatchlistScreen() {
  const { palette } = useTheme();
  const { data } = useWatchlist();
  const removeEvent = useRemoveEvent();
  const removeFighter = useRemoveFighter();
  const { tab } = useWatchlistStore();

  const hasEvents = (data?.events ?? []).length > 0;
  const hasFighters = (data?.fighters ?? []).length > 0;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[st.header, { borderBottomColor: palette.surface.border }]}>
        <TouchableOpacity onPress={() => useWatchlistStore.setState({ tab: 'events' })} style={[st.tabBtn, tab === 'events' && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
          <Text style={[typography.body, { color: tab === 'events' ? palette.text.primary : palette.text.tertiary, fontWeight: '600' }]}>Events</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => useWatchlistStore.setState({ tab: 'fighters' })} style={[st.tabBtn, tab === 'fighters' && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
          <Text style={[typography.body, { color: tab === 'fighters' ? palette.text.primary : palette.text.tertiary, fontWeight: '600' }]}>Fighters</Text>
        </TouchableOpacity>
      </View>

      {tab === 'events' && (
        <FlatList
          data={data?.events ?? []}
          keyExtractor={(e) => e.id}
          ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>No watched events. Tap "Watch" on any event to add it.</Text>}
          renderItem={({ item }) => (
            <View style={[st.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.name}</Text>
                <Text style={[typography.caption, { color: palette.text.secondary }]}>{new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</Text>
              </View>
              <TouchableOpacity onPress={() => removeEvent.mutate(item.id)}><Text style={{ color: '#EF4444', fontSize: 14 }}>Remove</Text></TouchableOpacity>
            </View>
          )}
        />
      )}
      {tab === 'fighters' && (
        <FlatList
          data={data?.fighters ?? []}
          keyExtractor={(f) => f.id}
          ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>No favorite fighters. Tap ♡ on any fighter to add them.</Text>}
          renderItem={({ item }) => (
            <View style={[st.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.fullName || item.lastName}</Text>
                <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.record || ''}{item.weightClass ? ` • ${item.weightClass}` : ''}</Text>
              </View>
              <TouchableOpacity onPress={() => removeFighter.mutate(item.id)}><Text style={{ color: '#EF4444', fontSize: 14 }}>Remove</Text></TouchableOpacity>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  header: { flexDirection: 'row', borderBottomWidth: 0.5 },
  tabBtn: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5 },
});
