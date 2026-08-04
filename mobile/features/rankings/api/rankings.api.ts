/** Rankings API — 13 endpoints */

import api from '@/services/api';

export const rankingsApi = {
  p4p: () => api.get('/v1/rankings/p4p'),
  byDivision: (division: string) => api.get(`/v1/rankings/${encodeURIComponent(division)}`),
  list: (params?: { type?: string; weight_class?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set('type', params.type);
    if (params?.weight_class) q.set('weight_class', params.weight_class);
    if (params?.limit) q.set('limit', String(params.limit));
    return api.get(`/v1/rankings?${q.toString()}`);
  },
  history: (fighterId: string) => api.get(`/v1/rankings/history/${fighterId}`),
  goat: () => api.get('/v1/rankings/goat'),
  prospects: (division?: string) => api.get(`/v1/rankings/prospects${division ? `?division=${encodeURIComponent(division)}` : ''}`),
  movement: (params?: { direction?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.direction) q.set('direction', params.direction);
    if (params?.limit) q.set('limit', String(params.limit ?? 20));
    return api.get(`/v1/rankings/movement?${q.toString()}`);
  },
  streaks: () => api.get('/v1/rankings/streaks'),
  champions: () => api.get('/v1/champions'),
  championsHistory: (weightClass?: string) => api.get(`/v1/champions/history${weightClass ? `?weight_class=${encodeURIComponent(weightClass)}` : ''}`),
  titleDefenses: () => api.get('/v1/title-defenses'),
  elo: (params?: { weightClass?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.weightClass) q.set('weight_class', params.weightClass);
    if (params?.limit) q.set('limit', String(params.limit ?? 50));
    return api.get(`/v1/elo?${q.toString()}`);
  },
  composite: (params?: { weightClass?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.weightClass) q.set('weight_class', params.weightClass);
    if (params?.limit) q.set('limit', String(params.limit ?? 50));
    return api.get(`/v1/composite?${q.toString()}`);
  },
};
