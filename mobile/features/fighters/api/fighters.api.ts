/** Fighters API layer — real endpoints only */

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
  search: (query: string) => api.get(`/v1/fighters?search=${encodeURIComponent(query)}`),
};

export const statsApi = {
  detail: (id: string) => api.get(`/v1/fighters/${id}/statistics`),
};

export const historyApi = {
  list: (id: string, params?: { result?: string; page?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.result) q.set('result', params.result);
    if (params?.page) q.set('page', String(params.page));
    if (params?.limit) q.set('limit', String(params.limit ?? 20));
    return api.get(`/v1/fighters/${id}/history?${q.toString()}`);
  },
};

export const similarityApi = {
  list: (id: string, limit = 10) => api.get(`/v1/fighters/${id}/similar?limit=${limit}`),
};

export const favoritesApi = {
  list: () => api.get('/v1/me/favorites'),
};
