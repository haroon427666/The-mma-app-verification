/** Watchlist Module — types, API, repo, hooks, store, nav, screen, components, theme */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';

// ── Types ──
export type WTab = 'events' | 'fighters' | 'fights' | 'promotions';
export interface WatchItem { id: string; title: string; subtitle: string | null; date: string | null; imageUrl: string | null; }
export interface WatchReminder { id: string; targetId: string; type: WTab; remindAt: string; active: boolean; }

// ── API ──
export const watchApi = {
  list: (type: WTab) => api.get(`/v1/watchlist/${type}`),
  add: (type: WTab, id: string) => api.post(`/v1/watchlist/${type}/${id}`),
  remove: (type: WTab, id: string) => api.delete(`/v1/watchlist/${type}/${id}`),
  reminders: () => api.get('/v1/watchlist/reminders'),
  createReminder: (targetId: string, type: WTab, remindAt: string) => api.post('/v1/watchlist/reminders', { target_id: targetId, type, remind_at: remindAt }),
  cancelReminder: (id: string) => api.delete(`/v1/watchlist/reminders/${id}`),
};

// ── Repository ──
export const watchRepo = {
  list: async (type: WTab) => { const { data } = await watchApi.list(type); return (data?.data ?? data) as WatchItem[]; },
  add: async (type: WTab, id: string) => { await watchApi.add(type, id); },
  remove: async (type: WTab, id: string) => { await watchApi.remove(type, id); },
  reminders: async () => { const { data } = await watchApi.reminders(); return (data?.data ?? data) as WatchReminder[]; },
  createReminder: async (targetId: string, type: WTab, remindAt: string) => { const { data } = await watchApi.createReminder(targetId, type, remindAt); return data as WatchReminder; },
  cancelReminder: async (id: string) => { await watchApi.cancelReminder(id); },
};

// ── Services ──
export const watchKeys = { all: ['watchlist'] as const, list: (t: WTab) => [...watchKeys.all, 'list', t] as const, reminders: () => [...watchKeys.all, 'reminders'] as const };
export const watchCache = { stale: 5 * 60_000, reminderStale: 60_000 };

// ── Store ──
export const useWatchStore = create<{ tab: WTab }>(() => ({ tab: 'events' }));

// ── Hooks ──
export function useWatchlist(tab: WTab) { return useQuery<WatchItem[]>({ queryKey: watchKeys.list(tab), queryFn: () => watchRepo.list(tab), staleTime: watchCache.stale }); }
export function useWatchReminders() { return useQuery<WatchReminder[]>({ queryKey: watchKeys.reminders(), queryFn: watchRepo.reminders, staleTime: watchCache.reminderStale }); }
export function useAddToWatchlist() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ type, id }: { type: WTab; id: string }) => watchRepo.add(type, id), onSettled: () => qc.invalidateQueries({ queryKey: watchKeys.all }) }); }
export function useRemoveFromWatchlist() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ type, id }: { type: WTab; id: string }) => watchRepo.remove(type, id), onMutate: async ({ type, id }) => { await qc.cancelQueries({ queryKey: watchKeys.list(type) }); const prev = qc.getQueryData<WatchItem[]>(watchKeys.list(type)); qc.setQueryData<WatchItem[]>(watchKeys.list(type), (old) => old?.filter((i) => i.id !== id)); return { prev, type }; }, onError: (_err, _vars, ctx) => { if (ctx) qc.setQueryData(watchKeys.list(ctx.type), ctx.prev); }, onSettled: () => qc.invalidateQueries({ queryKey: watchKeys.all }) }); }
export function useCreateReminder() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ targetId, type, remindAt }: { targetId: string; type: WTab; remindAt: string }) => watchRepo.createReminder(targetId, type, remindAt), onSettled: () => qc.invalidateQueries({ queryKey: watchKeys.reminders() }) }); }

// ── Navigation ──
const WStack = createNativeStackNavigator();
export function WatchlistStack() { return <WStack.Navigator screenOptions={{ headerShown: false }}><WStack.Screen name="Watchlist" component={WatchScreen} /></WStack.Navigator>; }

// ── Screen ──
export function WatchScreen() {
  const { palette } = useTheme();
  const { tab } = useWatchStore();
  const { data: items, isLoading, refetch } = useWatchlist(tab);
  const { data: reminders } = useWatchReminders();
  const removeMut = useRemoveFromWatchlist();
  const tabs: WTab[] = ['events', 'fighters'];

  return (
    <SafeAreaView style={[ws.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[ws.header, { borderBottomColor: palette.surface.border }]}>
        {tabs.map((t) => (
          <TouchableOpacity key={t} onPress={() => useWatchStore.setState({ tab: t })} style={[ws.tab, tab === t && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
            <Text style={[typography.bodySmall, { color: tab === t ? palette.primary[400] : palette.text.tertiary, fontWeight: '600', textTransform: 'capitalize' }]}>{t} ({((items ?? []).length)})</Text>
          </TouchableOpacity>
        ))}
      </View>
      {reminders && reminders.length > 0 && (
        <View style={[ws.reminderBar, { backgroundColor: '#F59E0B20', borderColor: '#F59E0B30' }]}>
          <Text style={[typography.caption, { color: '#F59E0B' }]}>🔔 {reminders.length} reminder{reminders.length > 1 ? 's' : ''} active</Text>
        </View>
      )}
      <FlatList data={items ?? []} keyExtractor={(i) => i.id} refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        renderItem={({ item }) => (
          <View style={[ws.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={{ flex: 1 }}>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.title}</Text>
              {item.subtitle && <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.subtitle}</Text>}
            </View>
            <TouchableOpacity onPress={() => removeMut.mutate({ type: tab, id: item.id })}><Text style={[typography.bodySmall, { color: '#EF4444' }]}>Remove</Text></TouchableOpacity>
          </View>
        )}
        ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>Your {tab} watchlist is empty</Text>}
      />
    </SafeAreaView>
  );
}

const ws = StyleSheet.create({
  root: { flex: 1 },
  header: { flexDirection: 'row', borderBottomWidth: 0.5 },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  reminderBar: { margin: spacing.lg, padding: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  card: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5 },
});
