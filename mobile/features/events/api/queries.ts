/** Events API endpoints + queries + mutations */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/services/api';
import type { Event, Fight } from '../../models';

const endpoints = {
  list: (status: string) => `/v1/events?status=${status}&limit=30`,
  detail: (id: string) => `/v1/events/${id}`,
  fights: (id: string) => `/v1/events/${id}/fights`,
  predictions: (id: string) => `/v1/predictions/event/${id}`,
  watch: (id: string) => `/v1/watchlist/events/${id}`,
  watched: '/v1/watchlist/events',
} as const;

export function useEvents(status: 'upcoming' | 'past') {
  const s = status === 'upcoming' ? 'SCHEDULED' : 'COMPLETED';
  return useQuery<Event[]>({
    queryKey: ['events', 'list', status],
    queryFn: async () => { const { data } = await api.get(endpoints.list(s)); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });
}

export function useEvent(id: string) {
  return useQuery<Event & { fights: Fight[] }>({
    queryKey: ['events', 'detail', id],
    queryFn: async () => {
      const [{ data: ev }, { data: fights }] = await Promise.all([
        api.get(endpoints.detail(id)), api.get(endpoints.fights(id)),
      ]);
      return { ...ev.data, fights: fights.data ?? [] };
    },
    enabled: !!id,
  });
}

export function useWatchEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ eventId, watch }: { eventId: string; watch: boolean }) => {
      if (watch) await api.post(endpoints.watch(eventId));
      else await api.delete(endpoints.watch(eventId));
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['events'] }),
  });
}

export function useWatchedEvents() {
  return useQuery<Event[]>({
    queryKey: ['events', 'watched'],
    queryFn: async () => { const { data } = await api.get(endpoints.watched); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });
}
