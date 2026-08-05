/** Rankings API — real endpoints only */

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
  goat: () => api.get('/v1/rankings/goat'),
  prospects: (division?: string) => api.get(`/v1/rankings/prospects${division ? `?division=${encodeURIComponent(division)}` : ''}`),
  movement: (params?: { division?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.division) q.set('division', params.division);
    if (params?.limit) q.set('limit', String(params.limit ?? 10));
    return api.get(`/v1/rankings/movement?${q.toString()}`);
  },
  streaks: () => api.get('/v1/rankings/streaks'),
  champions: () => api.get('/v1/champions'),
  titleDefenses: () => api.get('/v1/title-defenses'),
};
