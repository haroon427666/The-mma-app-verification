/** Events Repository — data access layer between API and hooks */

import { eventsApi } from '../api/events.api';
import { fightsApi } from '../api/fights.api';
import { predictionsApi } from '../api/predictions.api';
import { watchlistApi } from '../api/watchlist.api';
import { remindersApi } from '../api/reminders.api';
import type { ExtendedEvent, FightCardEntry, FightPrediction, Reminder } from '../types';

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

export const predictionsRepo = {
  forEvent: async (eventId: string) => {
    const { data } = await predictionsApi.forEvent(eventId);
    return (data ?? {}) as Record<string, FightPrediction>;
  },

  forFight: async (fightId: string) => {
    const { data } = await predictionsApi.forFight(fightId);
    return data as FightPrediction;
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

  check: async (eventId: string) => {
    const { data } = await watchlistApi.isWatched(eventId);
    return (data?.watched ?? false) as boolean;
  },
};

export const remindersRepo = {
  list: async () => {
    const { data } = await remindersApi.list();
    return (data?.data ?? []) as Reminder[];
  },

  create: async (eventId: string, remindAt: string, type: string) => {
    const { data } = await remindersApi.create(eventId, remindAt, type);
    return data as Reminder;
  },

  cancel: async (reminderId: string) => {
    await remindersApi.cancel(reminderId);
  },
};
