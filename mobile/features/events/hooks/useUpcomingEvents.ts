/** useUpcomingEvents */

import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '../api/events.api';

export function useUpcomingEvents(limit = 20) {
  return useQuery({
    queryKey: ['events', 'upcoming', limit],
    queryFn: async () => { const { data } = await eventsApi.upcoming(limit); return data.data ?? data ?? []; },
    staleTime: 5 * 60 * 1000,
  });
}
