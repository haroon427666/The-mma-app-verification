/** usePredictions — fight predictions for an event */

import { useQuery } from '@tanstack/react-query';
import { predictionsApi } from '../api/predictions.api';

export function usePredictions(eventId: string) {
  return useQuery({
    queryKey: ['events', 'predictions', eventId],
    queryFn: async () => { const { data } = await predictionsApi.forEvent(eventId); return data ?? {}; },
    staleTime: 30 * 60 * 1000,
    enabled: !!eventId,
  });
}
