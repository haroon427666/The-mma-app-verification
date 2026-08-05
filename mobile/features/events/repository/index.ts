/** Events Repository — data access layer between API and hooks */

import { eventsApi } from '../api/events.api';
import { fightsApi } from '../api/fights.api';
import { watchlistApi } from '../api/watchlist.api';
import type { ExtendedEvent, FightCardEntry } from '../types';

export const eventsRepo = {
  list: async (params: {
    status?: string; promotion?: string; page?: number; limit?: number;
  }) => {
    const { data } = await eventsApi.list(params);
    return (data?.data ?? data) as ExtendedEvent[];
  },

  getById: async (id: string) => {
    const { data } = await eventsApi.detail(id);
    return (data?.data ?? data) as ExtendedEvent;
  },

  getLive: async () => {
    const { data } = await eventsApi.live();
    return (data?.data ?? data) as ExtendedEvent[];
  },

  getUpcoming: async (limit = 20) => {
    const { data } = await eventsApi.upcoming(limit);
    return (data?.data ?? data) as ExtendedEvent[];
  },

  getPast: async (page = 1, limit = 20) => {
    const { data } = await eventsApi.past(page, limit);
    return (data?.data ?? data) as ExtendedEvent[];
  },
};

export const fightsRepo = {
  getCard: async (eventId: string) => {
    const { data } = await fightsApi.card(eventId);
    return (data?.data ?? data) as FightCardEntry[];
  },

  getResults: async (eventId: string) => {
    const { data } = await fightsApi.results(eventId);
    return data?.data ?? data;
  },

  getStatistics: async (eventId: string) => {
    const { data } = await fightsApi.statistics(eventId);
    return data?.data ?? data;
  },
};

export const watchlistRepo = {
  list: async () => {
    const { data } = await watchlistApi.list();
    return (data?.data ?? []) as string[];
  },

  add: async (eventId: string) => {
    await watchlistApi.add(eventId);
  },

  remove: async (eventId: string) => {
    await watchlistApi.remove(eventId);
  },
};
