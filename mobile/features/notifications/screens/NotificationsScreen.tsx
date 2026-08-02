/** Notifications module — inbox, mark read, optimistic updates, unread badge */

import React, { useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';

// ── Types ──
export interface NotificationItem {
  id: string; type: string; title: string; message: string; read: boolean;
  createdAt: string; payload: Record<string, unknown> | null;
}

// ── API + Repository ──
export const notificationsApi = {
  list: (limit = 50) => api.get(`/v1/notifications?limit=${limit}`),
  markRead: (id: string) => api.patch(`/v1/notifications/${id}/read`),
  markAllRead: () => api.patch('/v1/notifications/read-all'),
  delete: (id: string) => api.delete(`/v1/notifications/${id}`),
  badge: () => api.get('/v1/notifications?read=false&limit=1'),
};
export const notificationsRepo = {
  list: async (limit = 50) => { const { data } = await notificationsApi.list(limit); return (data?.data ?? data) as NotificationItem[]; },
  markRead: async (id: string) => { await notificationsApi.markRead(id); },
  markAllRead: async () => { await notificationsApi.markAllRead(); },
  delete: async (id: string) => { await notificationsApi.delete(id); },
  badge: async () => { const { data } = await notificationsApi.badge(); return data?.total ?? data?.count ?? 0; },
};

// ── Services ──
export const notificationKeys = {
  all: ['notifications'] as const,
  list: () => [...notificationKeys.all, 'list'] as const,
  badge: () => [...notificationKeys.all, 'badge'] as const,
};

// ── Store ──
export const useNotificationStore = create<{ filter: 'all' | 'unread'; unreadCount: number }>(() => ({ filter: 'all', unreadCount: 0 }));

// ── Hooks + Mutations ──
export function useNotifications() {
  return useQuery<NotificationItem[]>({
    queryKey: notificationKeys.list(), queryFn: () => notificationsRepo.list(), staleTime: 60_1000,
  });
}
export function useUnreadCount() {
  return useQuery({ queryKey: notificationKeys.badge(), queryFn: notificationsRepo.badge, staleTime: 30_1000, refetchInterval: 60_1000 });
}
export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificationsRepo.markRead(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: notificationKeys.list() });
      const prev = qc.getQueryData<NotificationItem[]>(notificationKeys.list());
      qc.setQueryData<NotificationItem[]>(notificationKeys.list(), (old) => old?.map((n) => n.id === id ? { ...n, read: true } : n));
      return { prev };
    },
    onError: (_err, _id, ctx) => { if (ctx?.prev) qc.setQueryData(notificationKeys.list(), ctx.prev); },
    onSettled: () => { qc.invalidateQueries({ queryKey: notificationKeys.list() }); qc.invalidateQueries({ queryKey: notificationKeys.badge() }); },
  });
}
export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsRepo.markAllRead(),
    onSuccess: () => { qc.invalidateQueries({ queryKey: notificationKeys.list() }); qc.invalidateQueries({ queryKey: notificationKeys.badge() }); },
  });
}
export function useDeleteNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificationsRepo.delete(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: notificationKeys.list() });
      const prev = qc.getQueryData<NotificationItem[]>(notificationKeys.list());
      qc.setQueryData<NotificationItem[]>(notificationKeys.list(), (old) => old?.filter((n) => n.id !== id));
      return { prev };
    },
    onError: (_err, _id, ctx) => { if (ctx?.prev) qc.setQueryData(notificationKeys.list(), ctx.prev); },
    onSettled: () => { qc.invalidateQueries({ queryKey: notificationKeys.list() }); qc.invalidateQueries({ queryKey: notificationKeys.badge() }); },
  });
}

// ── Screen ──
export function NotificationsScreen() {
  const { palette } = useTheme();
  const { data, isLoading, refetch } = useNotifications();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const deleteNotif = useDeleteNotification();
  const { filter } = useNotificationStore();
  const unreadCount = (data ?? []).filter((n) => !n.read).length;

  const filtered = (data ?? []).filter((n) => filter === 'unread' ? !n.read : true);

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[st.header, { borderBottomColor: palette.surface.border }]}>
        <Text style={[typography.headline, { color: palette.text.primary }]}>Alerts{unreadCount > 0 ? ` (${unreadCount})` : ''}</Text>
        {unreadCount > 0 && (
          <TouchableOpacity onPress={() => markAllRead.mutate()}>
            <Text style={[typography.bodySmall, { color: palette.primary[400], fontWeight: '600' }]}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>
      <FlatList
        data={filtered}
        keyExtractor={(n) => n.id}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => !item.read && markRead.mutate(item.id)} style={[st.notif, { backgroundColor: item.read ? 'transparent' : palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={[st.dot, { backgroundColor: item.read ? 'transparent' : palette.primary[400] }]} />
            <View style={{ flex: 1 }}>
              <Text style={[typography.bodySmall, { color: palette.primary[400], textTransform: 'uppercase' }]}>{item.type.replace(/_/g, ' ')}</Text>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: item.read ? '400' : '600' }]}>{item.title}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.message}</Text>
              <Text style={[typography.caption, { color: palette.text.tertiary, marginTop: 4 }]}>{new Date(item.createdAt).toLocaleDateString()}</Text>
            </View>
            <TouchableOpacity onPress={() => deleteNotif.mutate(item.id)} style={{ padding: 4 }}>
              <Text style={{ color: palette.text.tertiary }}>✕</Text>
            </TouchableOpacity>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>No notifications</Text>}
      />
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.lg, borderBottomWidth: 0.5 },
  notif: { flexDirection: 'row', alignItems: 'flex-start', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 2, borderRadius: radius.sm, borderWidth: 0.5 },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 12, marginTop: 6 },
});
