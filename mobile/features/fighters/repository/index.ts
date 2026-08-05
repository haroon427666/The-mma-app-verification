/** Fighters Repository — typed data access layer */

import { fightersApi, statsApi, historyApi, similarityApi, favoritesApi } from '../api/fighters.api';
import type { FighterProfile, FighterStats, FightHistoryEntry, SimilarFighter } from '../types';

export const fightersRepo = {
  list: async (params?: Parameters<typeof fightersApi.list>[0]) => {
    const { data } = await fightersApi.list(params);
    return (data?.data ?? data) as FighterProfile[];
  },
  getById: async (id: string) => {
    const { data } = await fightersApi.detail(id);
    return (data?.data ?? data) as FighterProfile;
  },
  search: async (query: string) => {
    const { data } = await fightersApi.search(query);
    return (data?.data ?? data) as FighterProfile[];
  },
};

export const statsRepo = {
  get: async (id: string) => { const { data } = await statsApi.detail(id); return (data?.data ?? data) as FighterStats; },
};

export const historyRepo = {
  list: async (id: string, params?: { result?: string; page?: number }) => {
    const { data } = await historyApi.list(id, params);
    return (data?.data ?? data) as FightHistoryEntry[];
  },
};

export const similarityRepo = {
  list: async (id: string, limit = 10) => {
    const { data } = await similarityApi.list(id, limit);
    return (data?.data ?? data) as SimilarFighter[];
  },
};

export const favoritesRepo = {
  listFighterIds: async (): Promise<string[]> => {
    const { data } = await favoritesApi.list();
    return data?.fighters ?? [];
  },
};
