/** Fighters Repository — typed data access layer */

import { fightersApi, statsApi, historyApi, rankingsApi, similarityApi, predictionApi, recommendationApi } from '../api/fighters.api';
import type { FighterProfile, FighterStats, FightHistoryEntry, SimilarFighter, StyleAnalysis, RankHistoryPoint, FighterComparison } from '../types';

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
  getTrending: async (limit = 10) => {
    const { data } = await fightersApi.trending(limit);
    return (data?.data ?? data) as FighterProfile[];
  },
  getChampions: async (weightClass?: string) => {
    const { data } = await fightersApi.champions(weightClass);
    return (data?.data ?? data) as FighterProfile[];
  },
};

export const statsRepo = {
  get: async (id: string) => { const { data } = await statsApi.detail(id); return (data?.data ?? data) as FighterStats; },
  striking: async (id: string) => { const { data } = await statsApi.striking(id); return data; },
  grappling: async (id: string) => { const { data } = await statsApi.grappling(id); return data; },
};

export const historyRepo = {
  list: async (id: string, params?: { result?: string; page?: number }) => {
    const { data } = await historyApi.list(id, params);
    return (data?.data ?? data) as FightHistoryEntry[];
  },
  timeline: async (id: string) => { const { data } = await historyApi.timeline(id); return data; },
  achievements: async (id: string) => { const { data } = await historyApi.achievements(id); return data; },
};

export const similarityRepo = {
  list: async (id: string, limit = 10) => {
    const { data } = await similarityApi.list(id, limit);
    return (data?.data ?? data) as SimilarFighter[];
  },
  breakdown: async (a: string, b: string) => { const { data } = await similarityApi.breakdown(a, b); return data; },
  styleAnalysis: async (id: string) => { const { data } = await similarityApi.styleAnalysis(id); return (data?.data ?? data) as StyleAnalysis; },
};

export const predictionRepo = {
  forFighter: async (id: string) => { const { data } = await predictionApi.forFighter(id); return data; },
  vsFighter: async (a: string, b: string) => {
    const { data } = await predictionApi.vsFighter(a, b);
    return data as FighterComparison['winnerPrediction'];
  },
};

export const recommendationRepo = {
  similarFighters: async (id: string) => { const { data } = await recommendationApi.similarFighters(id); return data; },
  becauseYouFollow: async (id: string) => { const { data } = await recommendationApi.becauseYouFollow(id); return data; },
};
