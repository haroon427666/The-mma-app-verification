/** Home hooks */

import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  useHomeFeed, useLiveEvents,
  useRecommendedFighters,
} from '../api/queries';
import { useHomeStore, homeActions } from '../store/homeStore';
import { useConnectivityStore } from '@/stores/connectivity';

export function useHome() {
  const feed = useHomeFeed();
  const { dismissedCards } = useHomeStore();
  const isOffline = useConnectivityStore((s) => s.status === 'offline');
  const qc = useQueryClient();

  const refresh = useCallback(() => {
    qc.invalidateQueries({ queryKey: ['home'] });
    homeActions.markRefreshed();
  }, [qc]);

  const dismiss = useCallback((id: string) => homeActions.dismissCard(id), []);

  const filteredSections = feed.data ? {
    ...feed.data,
    recommendedFighters: feed.data.recommendedFighters?.filter((f) => !dismissedCards.has(f.id)),
  } : undefined;

  return {
    feed: filteredSections,
    isLoading: feed.isLoading,
    isError: feed.isError,
    isOffline,
    refresh,
    dismiss,
    refetch: feed.refetch,
  };
}

export { useLiveEvents, useRecommendedFighters };
