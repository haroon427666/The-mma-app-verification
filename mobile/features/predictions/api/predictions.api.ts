/** Predictions API — all endpoints for prediction engine */

import api from '@/services/api';

export const predictionsApi = {
  forFight: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}`),
  forEvent: (eventId: string) => api.get(`/v1/predictions/event/${eventId}`),
  dashboard: () => api.get('/v1/predictions/dashboard'),
  highlights: (limit = 8) => api.get(`/v1/predictions/highlights?limit=${limit}`),
  history: (page = 1, limit = 20) => api.get(`/v1/predictions/history?page=${page}&limit=${limit}`),
  accuracy: () => api.get('/v1/predictions/accuracy'),
  matchup: (fAId: string, fBId: string) => api.get(`/v1/predictions/matchup?fighter_a=${fAId}&fighter_b=${fBId}`),
  monteCarlo: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}/monte-carlo`),
  factors: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}/factors`),
  odds: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}/odds`),
  save: (fightId: string) => api.post(`/v1/predictions/saved/${fightId}`),
  unsave: (fightId: string) => api.delete(`/v1/predictions/saved/${fightId}`),
  saved: () => api.get('/v1/predictions/saved'),
  share: (fightId: string) => api.post(`/v1/predictions/${fightId}/share`),
  compareOdds: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}/odds/compare`),
};
