/** useFightCard — sorted, grouped fight card for an event */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fightsApi } from '../api/fights.api';
import { sortFightCard, groupBySegment } from '../utils/fightSorter';

export function useFightCard(eventId: string) {
  const query = useQuery({
    queryKey: ['events', 'fightCard', eventId],
    queryFn: async () => { const { data } = await fightsApi.card(eventId); return data.data ?? data ?? []; },
    staleTime: 5 * 60 * 1000,
    enabled: !!eventId,
  });

  const fights = query.data ?? [];
  const sorted = useMemo(() => sortFightCard(fights), [fights]);
  const grouped = useMemo(() => groupBySegment(sorted), [sorted]);

  return { ...query, fights: sorted, grouped };
}
