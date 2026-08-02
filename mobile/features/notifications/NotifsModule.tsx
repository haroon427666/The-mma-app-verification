/** Notifications Module — inbox, categories, push, preferences, deep links */

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
export type NotifCategory = 'event' | 'fight' | 'ranking' | 'prediction' | 'recommendation' | 'watchlist' | 'system';
export interface Notification { id: string; category: NotifCategory; title: string; message: string; read: boolean; createdAt: string; deepLink: string | null; actionable: boolean; }
export interface NotifPreferences { pushEnabled: boolean; categories: Record<NotifCategory, boolean>; quietHours: { enabled: boolean; start: string; end: string }; digest: 'daily' | 'weekly' | 'never'; }

// ── API ──
export const notifApi = {
  list: (limit = 40) => api.get(`/v1/notifications?limit=${limit}`),
  markRead: (id: string) => api.patch(`/v1/notifications/${id}/read`),
  markAllRead: () => api.patch('/v1/notifications/read-all'),
  delete: (id: string) => api.delete(`/v1/notifications/${id}`),
  count: () => api.get('/v1/notifications/unread-count'),
  preferences: () => api.get('/v1/notifications/preferences'),
  updatePreferences: (p: Partial<NotifPreferences>) => api.put('/v1/notifications/preferences', p),
  registerToken: (token: string) => api.post('/v1/notifications/push-token', { token }),
};

// ── Repository ──
export const notifRepo = {
  list: async (limit = 40) => { const { data } = await notifApi.list(limit); return (data?.data ?? data) as Notification[]; },
  markRead: async (id: string) => { await notifApi.markRead(id); },
  markAllRead: async () => { await notifApi.markAllRead(); },
  delete: async (id: string) => { await notifApi.delete(id); },
  count: async () => { const { data } = await notifApi.count(); return (data?.count ?? 0) as number; },
  preferences: async () => { const { data } = await notifApi.preferences(); return (data?.data ?? data) as NotifPreferences; },
  updatePreferences: async (p: Partial<NotifPreferences>) => { await notifApi.updatePreferences(p); },
};

// ── Services ──
export const notifKeys = { all: ['notifications'] as const, list: () => [...notifKeys.all, 'list'] as const, count: () => [...notifKeys.all, 'count'] as const, prefs: () => [...notifKeys.all, 'prefs'] as const };
export const notifColors = { event: '#8B5CF6', fight: '#EF4444', ranking: '#F59E0B', prediction: '#3B82F6', recommendation: '#10B981', watchlist: '#F97316', system: '#6B7280' } as const;

// ── Store ──
export const useNotifStore = create<{ filter: 'all' | 'unread'; category: NotifCategory | null }>(() => ({ filter: 'all', category: null }));

// ── Hooks ──
export function useNotifications() { return useQuery<Notification[]>({ queryKey: notifKeys.list(), queryFn: () => notifRepo.list(), staleTime: 60_000 }); }
export function useUnreadCount() { return useQuery<number>({ queryKey: notifKeys.count(), queryFn: notifRepo.count, staleTime: 30_000, refetchInterval: 60_000 }); }
export function useMarkRead() { const qc = useQueryClient(); return useMutation({ mutationFn: (id: string) => notifRepo.markRead(id), onMutate: async (id) => { await qc.cancelQueries({ queryKey: notifKeys.list() }); qc.setQueryData<Notification[]>(notifKeys.list(), (old) => old?.map((n) => n.id === id ? { ...n, read: true } : n)); }, onSettled: () => qc.invalidateQueries({ queryKey: notifKeys.all }) }); }
export function useMarkAllRead() { const qc = useQueryClient(); return useMutation({ mutationFn: notifRepo.markAllRead, onSettled: () => qc.invalidateQueries({ queryKey: notifKeys.all }) }); }
export function useDeleteNotif() { const qc = useQueryClient(); return useMutation({ mutationFn: (id: string) => notifRepo.delete(id), onSettled: () => qc.invalidateQueries({ queryKey: notifKeys.all }) }); }

// ── Navigation ──
const NStack = createNativeStackNavigator();
export function NotificationsStack() { return <NStack.Navigator screenOptions={{ headerShown: false }}><NStack.Screen name="Notifs" component={NotifScreen} /></NStack.Navigator>; }

// ── Screen ──
export function NotifScreen() {
  const { palette } = useTheme();
  const { filter } = useNotifStore();
  const { data: notifs, isLoading, refetch } = useNotifications();
  const { data: unread } = useUnreadCount();
  const markRead = useMarkRead();
  const markAll = useMarkAllRead();
  const del = useDeleteNotif();

  const filtered = (notifs ?? []).filter((n) => filter === 'unread' ? !n.read : true);
  const cats: NotifCategory[] = ['event', 'fight', 'ranking', 'prediction', 'recommendation', 'watchlist', 'system'];

  return (
    <SafeAreaView style={[ns.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[ns.header, { borderBottomColor: palette.surface.border }]}>
        <Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>Alerts {unread ? `(${unread})` : ''}</Text>
        <View style={ns.actions}>
          <TouchableOpacity onPress={() => useNotifStore.setState({ filter: filter === 'all' ? 'unread' : 'all' })}><Text style={[typography.bodySmall, { color: palette.primary[400], marginRight: 16 }]}>{filter === 'all' ? 'Unread' : 'All'}</Text></TouchableOpacity>
          {unread ? <TouchableOpacity onPress={() => markAll.mutate()}><Text style={[typography.bodySmall, { color: palette.primary[400] }]}>Read all</Text></TouchableOpacity> : null}
        </View>
      </View>
      <FlatList horizontal data={cats} showsHorizontalScrollIndicator={false} contentContainerStyle={ns.chipRow} keyExtractor={(c) => c}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => useNotifStore.setState({ category: useNotifStore.getState().category === item ? null : item })}
            style={[ns.chip, { backgroundColor: useNotifStore.getState().category === item ? notifColors[item] : palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.caption, { color: useNotifStore.getState().category === item ? '#FFF' : palette.text.secondary, textTransform: 'capitalize' }]}>{item}</Text>
          </TouchableOpacity>
        )}
      />

      <FlatList data={filtered} keyExtractor={(n) => n.id} refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => { if (!item.read) markRead.mutate(item.id); }}
            style={[ns.row, { backgroundColor: item.read ? 'transparent' : palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={[ns.dot, { backgroundColor: item.read ? 'transparent' : palette.primary[400] }]} />
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={[ns.badge, { backgroundColor: notifColors[item.category] }]}><Text style={{ color: '#FFF', fontSize: 9, fontWeight: '700', textTransform: 'uppercase' }}>{item.category}</Text></View>
              </View>
              <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: item.read ? '400' : '600', marginTop: 4 }]}>{item.title}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.message}</Text>
              <Text style={[typography.caption, { color: palette.text.tertiary, marginTop: 4 }]}>{new Date(item.createdAt).toLocaleDateString()}</Text>
            </View>
            <TouchableOpacity onPress={() => del.mutate(item.id)}><Text style={{ color: palette.text.tertiary }}>✕</Text></TouchableOpacity>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>No notifications</Text>}
      />
    </SafeAreaView>
  );
}

const ns = StyleSheet.create({
  root: { flex: 1 }, header: { borderBottomWidth: 0.5 }, actions: { flexDirection: 'row', paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  chipRow: { paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, gap: 6 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 0.5 },
  row: { flexDirection: 'row', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 2, borderRadius: radius.sm, borderWidth: 0.5 },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 12, marginTop: 6 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
});
