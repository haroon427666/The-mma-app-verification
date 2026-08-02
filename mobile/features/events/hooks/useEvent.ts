/** useEvent — single event with fights, stats, bonuses */

import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '../api/events.api';
import { fightsApi } from '../api/fights.api';
import type { ExtendedEvent } from '../types';

export function useEvent(id: string) {
  return useQuery<ExtendedEvent>({
    queryKey: ['events', 'detail', id],
    queryFn: async () => {
      const [{ data: ev }, { data: fights }, { data: stats }, { data: results }] = await Promise.all([
        eventsApi.detail(id),
        fightsApi.card(id),
        fightsApi.statistics(id),
        fightsApi.results(id),
      ]);
      return {
        ...(ev.data ?? ev),
        fights: (fights.data ?? fights) ?? [],
        statistics: (stats.data ?? stats) ?? null,
        results: (results.data ?? results) ?? null,
      } as ExtendedEvent;
    },
    staleTime: 5 * 60 * 1000,
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data as ExtendedEvent | undefined;
      return data?.isLive ? 30_000 : false;
    },
  });
}
