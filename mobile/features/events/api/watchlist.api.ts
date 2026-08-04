/** Watchlist API */

import api from '@/services/api';

export const watchlistApi = {
  list: () => api.get('/v1/me/watchlist/events'),
  add: (eventId: string) => api.post(`/v1/me/watchlist/events/${eventId}`),
  remove: (eventId: string) => api.delete(`/v1/me/watchlist/events/${eventId}`),
  isWatched: (eventId: string) => api.get(`/v1/me/watchlist/events/${eventId}/status`),
} as const;
