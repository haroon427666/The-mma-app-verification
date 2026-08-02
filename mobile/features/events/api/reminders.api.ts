/** Reminders API */

import api from '@/services/api';

export const remindersApi = {
  list: () => api.get('/v1/reminders'),
  create: (eventId: string, remindAt: string, type: string) =>
    api.post('/v1/reminders', { event_id: eventId, remind_at: remindAt, type }),
  cancel: (reminderId: string) => api.delete(`/v1/reminders/${reminderId}`),
} as const;
