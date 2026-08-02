/** Fighters API layer — 7 domain-specific API files */

import api from '@/services/api';

export const fightersApi = {
  list: (params: { weightClass?: string; search?: string; filter?: string; sort?: string; page?: number; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.weightClass) q.set('weight_class', params.weightClass);
    if (params.search) q.set('search', params.search);
    if (params.filter) q.set('filter', params.filter);
    if (params.sort) q.set('sort', params.sort);
    if (params.page) q.set('page', String(params.page));
    if (params.limit) q.set('limit', String(params.limit ?? 50));
    return api.get(`/v1/fighters?${q.toString()}`);
  },
  detail: (id: string) => api.get(`/v1/fighters/${id}`),
  search: (query: string) => api.get(`/v1/fighters/search?q=${encodeURIComponent(query)}`),
  trending: (limit = 10) => api.get(`/v1/fighters/trending?limit=${limit}`),
  champions: (weightClass?: string) => api.get(`/v1/fighters/champions${weightClass ? `?weight_class=${encodeURIComponent(weightClass)}` : ''}`),
};

export const statsApi = {
  detail: (id: string) => api.get(`/v1/fighters/${id}/stats`),
  striking: (id: string) => api.get(`/v1/fighters/${id}/stats/striking`),
  grappling: (id: string) => api.get(`/v1/fighters/${id}/stats/grappling`),
};

export const historyApi = {
  list: (id: string, params?: { result?: string; page?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.result) q.set('result', params.result);
    if (params?.page) q.set('page', String(params.page));
    if (params?.limit) q.set('limit', String(params.limit ?? 20));
    return api.get(`/v1/fighters/${id}/fights?${q.toString()}`);
  },
  timeline: (id: string) => api.get(`/v1/fighters/${id}/timeline`),
  achievements: (id: string) => api.get(`/v1/fighters/${id}/achievements`),
};

export const rankingsApi = {
  history: (id: string) => api.get(`/v1/fighters/${id}/rankings/history`),
  current: (id: string) => api.get(`/v1/fighters/${id}/rankings`),
  best: (id: string) => api.get(`/v1/fighters/${id}/rankings/best`),
};

export const similarityApi = {
  list: (id: string, limit = 10) => api.get(`/v1/fighters/${id}/similar?limit=${limit}`),
  breakdown: (fighterA: string, fighterB: string) => api.get(`/v1/fighters/similarity?fighter_a=${fighterA}&fighter_b=${fighterB}`),
  styleAnalysis: (id: string) => api.get(`/v1/fighters/${id}/style-analysis`),
};

export const predictionApi = {
  forFighter: (id: string) => api.get(`/v1/predictions/fighter/${id}`),
  vsFighter: (fighterA: string, fighterB: string) => api.get(`/v1/predictions/matchup?fighter_a=${fighterA}&fighter_b=${fighterB}`),
};

export const recommendationApi = {
  similarFighters: (id: string) => api.get(`/v1/recommendations/fighters/similar?fighter_id=${id}`),
  becauseYouFollow: (id: string) => api.get(`/v1/recommendations/fighters/because?fighter_id=${id}`),
};
