/** Fights API */

import api from '@/services/api';

export const fightsApi = {
  card: (eventId: string) => api.get(`/v1/events/${eventId}/fights`),
  results: (eventId: string) => api.get(`/v1/events/${eventId}/results`),
  statistics: (eventId: string) => api.get(`/v1/events/${eventId}/statistics`),
  detail: (fightId: string) => api.get(`/v1/fights/${fightId}`),
} as const;
