/** usePastEvents — paginated past events */

import { useInfiniteQuery } from '@tanstack/react-query';
import { eventsApi } from '../api/events.api';

export function usePastEvents() {
  return useInfiniteQuery({
    queryKey: ['events', 'past'],
    queryFn: async ({ pageParam = 1 }) => {
      const { data } = await eventsApi.past(pageParam as number, 20);
      return data.data ?? data ?? [];
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) =>
      Array.isArray(lastPage) && lastPage.length === 20 ? pages.length + 1 : undefined,
    staleTime: 24 * 60 * 60 * 1000,
  });
}
