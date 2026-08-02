/** useLiveEvents — polls every 30s */

import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '../api/events.api';

export function useLiveEvents() {
  return useQuery({
    queryKey: ['events', 'live'],
    queryFn: async () => { const { data } = await eventsApi.live(); return data.data ?? data ?? []; },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}
