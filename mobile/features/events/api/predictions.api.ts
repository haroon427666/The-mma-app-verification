/** Predictions API for events */

import api from '@/services/api';

export const predictionsApi = {
  forEvent: (eventId: string) => api.get(`/v1/predictions/event/${eventId}`),
  forFight: (fightId: string) => api.get(`/v1/predictions/fight/${fightId}`),
  highlights: () => api.get('/v1/predictions/highlights'),
} as const;
