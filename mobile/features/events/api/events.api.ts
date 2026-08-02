/** Events API — all event-related endpoints with configurable params */

import api from '@/services/api';

const BASE = '/v1/events';

export const eventsApi = {
  list: (params: { status?: string; promotion?: string; page?: number; limit?: number; from?: string; to?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.status) q.set('status', params.status);
    if (params.promotion) q.set('promotion', params.promotion);
    if (params.page) q.set('page', String(params.page));
    if (params.limit) q.set('limit', String(params.limit));
    if (params.from) q.set('from', params.from);
    if (params.to) q.set('to', params.to);
    return api.get(`${BASE}?${q.toString()}`);
  },
  detail: (id: string) => api.get(`${BASE}/${id}`),
  live: () => api.get(`${BASE}/live`),
  upcoming: (limit = 20) => api.get(`${BASE}/upcoming?limit=${limit}`),
  past: (page = 1, limit = 20) => api.get(`${BASE}/past?page=${page}&limit=${limit}`),
  search: (query: string) => api.get(`${BASE}?search=${encodeURIComponent(query)}`),
} as const;
