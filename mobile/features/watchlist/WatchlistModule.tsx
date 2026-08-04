/** Watchlist Module — fighters, events, promotions, reminders, offline sync, collections */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import React, { useState } from 'react';
import { View, Text, FlatList, SectionList, TouchableOpacity, StyleSheet, RefreshControl, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius, shadows } from '@/theme';
import type { Fighter, Event, Fight } from '../models';

// ── Types ──
export type WatchlistTab = 'events' | 'fighters' | 'fights' | 'promotions';
export type WatchlistSort = 'date' | 'name' | 'added';
export interface WatchlistReminder { id: string; targetId: string; type: WatchlistTab; remindAt: string; active: boolean; }
export interface WatchlistCollection { id: string; name: string; items: string[]; type: WatchlistTab; }

// ── API ──
// ── API ──
const watchlistPath = (type: WatchlistTab) =>
  type === 'events' ? '/v1/me/watchlist/events'
  : type === 'fighters' ? '/v1/me/favorites/fighters'
  : `/v1/watchlist/${type}`; // phantom tab — no backend route, reported in contract diff

export const watchlistApi = {
  list: (type: WatchlistTab) => api.get(watchlistPath(type)),
  add: (type: WatchlistTab, id: string) => api.post(`${watchlistPath(type)}/${id}`),
  remove: (type: WatchlistTab, id: string) => api.delete(`${watchlistPath(type)}/${id}`),
  check: (type: WatchlistTab, id: string) => api.get(`${watchlistPath(type)}/${id}/status`),
  reminders: () => api.get('/v1/watchlist/reminders'),
  createReminder: (targetId: string, type: WatchlistTab, remindAt: string) => api.post('/v1/watchlist/reminders', { target_id: targetId, type, remind_at: remindAt }),
  cancelReminder: (id: string) => api.delete(`/v1/watchlist/reminders/${id}`),
  collections: () => api.get('/v1/watchlist/collections'),
  createCollection: (name: string, type: WatchlistTab) => api.post('/v1/watchlist/collections', { name, type }),
  bulkAdd: (type: WatchlistTab, ids: string[]) => api.post(`/v1/watchlist/${type}/bulk`, { ids }),
  bulkRemove: (type: WatchlistTab, ids: string[]) => api.delete(`/v1/watchlist/${type}/bulk`, { data: { ids } }),
};

// ── Repository ──
export const watchlistRepo = {
  list: async (type: WatchlistTab) => { const { data } = await watchlistApi.list(type); return (data?.data ?? data); },
  add: async (type: WatchlistTab, id: string) => { await watchlistApi.add(type, id); },
  remove: async (type: WatchlistTab, id: string) => { await watchlistApi.remove(type, id); },
  check: async (type: WatchlistTab, id: string) => { const { data } = await watchlistApi.check(type, id); return data?.watched ?? false; },
  reminders: async () => { const { data } = await watchlistApi.reminders(); return (data?.data ?? data) as WatchlistReminder[]; },
  createReminder: async (targetId: string, type: WatchlistTab, remindAt: string) => { const { data } = await watchlistApi.createReminder(targetId, type, remindAt); return data as WatchlistReminder; },
  cancelReminder: async (id: string) => { await watchlistApi.cancelReminder(id); },
  collections: async () => { const { data } = await watchlistApi.collections(); return (data?.data ?? data) as WatchlistCollection[]; },
  createCollection: async (name: string, type: WatchlistTab) => { const { data } = await watchlistApi.createCollection(name, type); return data as WatchlistCollection; },
  bulkAdd: async (type: WatchlistTab, ids: string[]) => { await watchlistApi.bulkAdd(type, ids); },
  bulkRemove: async (type: WatchlistTab, ids: string[]) => { await watchlistApi.bulkRemove(type, ids); },
};

// ── Services ──
export const watchlistKeys = {
  all: ['watchlist'] as const,
  list: (type: WatchlistTab) => [...watchlistKeys.all, 'list', type] as const,
  check: (type: WatchlistTab, id: string) => [...watchlistKeys.all, 'check', type, id] as const,
  reminders: () => [...watchlistKeys.all, 'reminders'] as const,
  collections: () => [...watchlistKeys.all, 'collections'] as const,
};
export const watchlistCache = { stale: 5 * 60_000, checkStale: 30_000 };
export const watchlistAnalytics = {
  itemAdded: (type: string, id: string) => { if (__DEV__) console.log('[analytics] watchlist_added', { type, id }); },
  itemRemoved: (type: string, id: string) => { if (__DEV__) console.log('[analytics] watchlist_removed', { type, id }); },
  reminderCreated: (targetId: string) => { if (__DEV__) console.log('[analytics] reminder_created', { targetId }); },
};

// ── Store ──
export const useWatchlistStore = create<{ tab: WatchlistTab; sortBy: WatchlistSort; selectedIds: Set<string> }>(() => ({ tab: 'events', sortBy: 'date', selectedIds: new Set() }));
export const watchlistActions = {
  setTab: (t: WatchlistTab) => useWatchlistStore.setState({ tab: t }),
  toggleSelect: (id: string) => useWatchlistStore.setState((s) => { const n = new Set(s.selectedIds); n.has(id) ? n.delete(id) : n.add(id); return { selectedIds: n }; }),
  clearSelection: () => useWatchlistStore.setState({ selectedIds: new Set() }),
};

// ── Hooks ──
export function useWatchlistItems(type: WatchlistTab) { return useQuery({ queryKey: watchlistKeys.list(type), queryFn: () => watchlistRepo.list(type), staleTime: watchlistCache.stale }); }
export function useIsWatched(type: WatchlistTab, id: string) { return useQuery({ queryKey: watchlistKeys.check(type, id), queryFn: () => watchlistRepo.check(type, id), staleTime: watchlistCache.checkStale, enabled: !!id }); }
export function useAddToWatchlist() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ type, id }: { type: WatchlistTab; id: string }) => watchlistRepo.add(type, id), onSuccess: (_d, v) => { watchlistAnalytics.itemAdded(v.type, v.id); qc.invalidateQueries({ queryKey: watchlistKeys.all }); } }); }
export function useRemoveFromWatchlist() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ type, id }: { type: WatchlistTab; id: string }) => watchlistRepo.remove(type, id), onSuccess: (_d, v) => { watchlistAnalytics.itemRemoved(v.type, v.id); qc.invalidateQueries({ queryKey: watchlistKeys.all }); } }); }
export function useWatchlistReminders() { return useQuery({ queryKey: watchlistKeys.reminders(), queryFn: watchlistRepo.reminders, staleTime: 60_000 }); }
export function useCreateReminder() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ targetId, type, remindAt }: { targetId: string; type: WatchlistTab; remindAt: string }) => watchlistRepo.createReminder(targetId, type, remindAt), onSuccess: (_d, v) => { watchlistAnalytics.reminderCreated(v.targetId); qc.invalidateQueries({ queryKey: watchlistKeys.reminders() }); } }); }
export function useCancelReminder() { const qc = useQueryClient(); return useMutation({ mutationFn: (id: string) => watchlistRepo.cancelReminder(id), onSettled: () => qc.invalidateQueries({ queryKey: watchlistKeys.reminders() }) }); }

// ── Navigation ──
type WatchlistStackParamList = { WatchlistHome: undefined };
const WStack = createNativeStackNavigator<WatchlistStackParamList>();
export function WatchlistStack() { return <WStack.Navigator screenOptions={{ headerShown: false }}><WStack.Screen name="WatchlistHome" component={WatchlistScreen} /></WStack.Navigator>; }

// ── Screen ──
export function WatchlistScreen() {
  const { palette } = useTheme();
  const { tab, selectedIds } = useWatchlistStore();
  const { data: items, isLoading, refetch } = useWatchlistItems(tab);
  const { data: reminders } = useWatchlistReminders();
  const addMutation = useAddToWatchlist();
  const removeMutation = useRemoveFromWatchlist();

  const tabs: WatchlistTab[] = ['events', 'fighters', 'fights', 'promotions'];
  const itemList: any[] = items ?? [];

  return (
    <SafeAreaView style={[wl.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[wl.header, { borderBottomColor: palette.surface.border }]}>
        {tabs.map((t) => (
          <TouchableOpacity key={t} onPress={() => watchlistActions.setTab(t)} style={[wl.tab, tab === t && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
            <Text style={[typography.bodySmall, { color: tab === t ? palette.primary[400] : palette.text.tertiary, fontWeight: '600', textTransform: 'capitalize' }]}>{t}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {reminders && reminders.length > 0 && (
        <View style={[wl.reminderBar, { backgroundColor: '#F59E0B20', borderColor: '#F59E0B30' }]}>
          <Text style={[typography.caption, { color: '#F59E0B' }]}>🔔 {reminders.length} active reminder{reminders.length > 1 ? 's' : ''}</Text>
        </View>
      )}

      <FlatList
        data={itemList}
        keyExtractor={(item: any) => item.id}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>{tab.charAt(0).toUpperCase() + tab.slice(1)} ({itemList.length})</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity style={[wl.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={{ flex: 1 }}>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.title || item.fullName || item.name}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.subtitle || item.record || item.date || ''}</Text>
            </View>
            <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
              {selectedIds.has(item.id) && <Text style={{ color: '#3B82F6' }}>✓</Text>}
              <TouchableOpacity onPress={() => removeMutation.mutate({ type: tab, id: item.id })}>
                <Text style={[typography.bodySmall, { color: '#EF4444' }]}>Remove</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>Your {tab} watchlist is empty. Browse fighters and events to add them.</Text>}
      />
    </SafeAreaView>
  );
}

// ── Theme + Accessibility ──
export const watchlistColors = { tabActive: '#3B82F6', removeButton: '#EF4444', reminderBar: '#F59E0B' } as const;
export const watchlistLabels = { add: 'Add to watchlist', remove: 'Remove from watchlist', reminder: 'Set reminder for this item' };
export function WatchlistSkeleton() { return <View style={{ padding: spacing.lg, gap: 12 }}>{[1,2,3,4].map((i) => <View key={i} style={{ height: 72, backgroundColor: '#1A1A2E', borderRadius: radius.md }} />)}</View>; }

const wl = StyleSheet.create({
  root: { flex: 1 },
  header: { flexDirection: 'row', borderBottomWidth: 0.5 },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  reminderBar: { margin: spacing.lg, padding: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  card: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5 },
});
