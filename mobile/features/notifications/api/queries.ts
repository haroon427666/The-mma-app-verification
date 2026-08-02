/** Notifications API + store */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import type { Notification } from '../../models';

export function useNotifications() {
  return useQuery<Notification[]>({
    queryKey: ['notifications'],
    queryFn: async () => { const { data } = await api.get('/v1/notifications?limit=50'); return data.data ?? []; },
    staleTime: 60 * 1000,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.patch(`/v1/notifications/${id}/read`),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['notifications'] });
      const prev = qc.getQueryData<Notification[]>(['notifications']);
      qc.setQueryData<Notification[]>(['notifications'], (old) =>
        old?.map((n) => n.id === id ? { ...n, read: true } : n));
      return { prev };
    },
    onError: (_err, _id, ctx) => { if (ctx?.prev) qc.setQueryData(['notifications'], ctx.prev); },
    onSettled: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.patch('/v1/notifications/read-all'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export const useNotificationStore = create<{ filter: 'all' | 'unread' }>(() => ({ filter: 'all' }));
