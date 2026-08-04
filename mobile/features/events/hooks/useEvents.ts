/** useEvents — paginated/infinite event list (via repository layer) */

import { useInfiniteQuery } from '@tanstack/react-query';
import { eventsRepo } from '../repository';
import { eventKeys } from '../services/queryKeys';
import type { ExtendedEvent } from '../types';

export function useEvents() {
  return useInfiniteQuery<ExtendedEvent[]>({
    queryKey: eventKeys.lists(),
    queryFn: async ({ pageParam }) => {
      const items = await eventsRepo.list({ page: pageParam as number, limit: 30 });
      return items ?? [];
    },
    getNextPageParam: (lastPage, allPages) =>
      lastPage && lastPage.length > 0 ? allPages.length + 1 : undefined,
    initialPageParam: 1,
  });
}

// Note: other events hooks live in their own files; see ./index.ts