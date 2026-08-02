/** Production Refresh System — standardized pull-to-refresh across the entire app.

Usage:
  const { refresh, isRefreshing } = useRefresh(['fighters', 'list'], 'refreshKey');
  <FlatList refreshControl={<RefreshControl refreshing={isRefreshing} onRefresh={refresh} />} />
*/

import { useCallback, useRef, useState } from 'react';
import { useQueryClient, onlineManager } from '@tanstack/react-query';

interface RefreshConfig {
  /** Query key patterns to invalidate (fuzzy match via prefix) */
  invalidateKeys?: readonly unknown[][];
  /** Exact query keys to refetch after invalidation */
  refetchKeys?: readonly unknown[][];
  /** Minimum duration to show spinner (prevents flicker) */
  minDurationMs?: number;
  /** Max wait time before forcing spinner off */
  maxDurationMs?: number;
}

export function useRefresh(
  /** Descriptive key for logging/analytics */
  screenName: string,
  config: RefreshConfig = {},
) {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    // Cancel any in-flight refresh
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    // Respect offline mode — don't attempt refresh if offline
    if (!onlineManager.isOnline()) {
      return; // Silently skip — offline banner already shows
    }

    setIsRefreshing(true);
    const start = Date.now();
    const minDuration = config.minDurationMs ?? 300;

    try {
      // 1. Invalidate affected queries
      if (config.invalidateKeys) {
        for (const key of config.invalidateKeys) {
          await queryClient.invalidateQueries({ queryKey: key });
        }
      } else {
        // Default: invalidate all queries for this screen
        await queryClient.invalidateQueries({ queryKey: [screenName] });
      }

      // 2. Refetch exact keys
      if (config.refetchKeys) {
        await Promise.all(config.refetchKeys.map(
          key => queryClient.refetchQueries({ queryKey: key }),
        ));
      } else {
        await queryClient.refetchQueries({ queryKey: [screenName] });
      }

    } catch {
      // Silently fail — error state is handled per-query
    } finally {
      // Enforce min duration to prevent flicker
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, minDuration - elapsed);
      if (remaining > 0) {
        await new Promise(r => setTimeout(r, remaining));
      }
      setIsRefreshing(false);
    }
  }, [queryClient, screenName, config]);

  return { refresh, isRefreshing };
}

// ═══════════════════════════════════════════════════════════════════════════
// Pre-built refresh configs per screen
// ═══════════════════════════════════════════════════════════════════════════

export const screenRefreshes = {
  home: {
    invalidateKeys: [['home'], ['events', 'live'], ['events', 'upcoming'], ['trending'], ['recommendations']] as const,
  },
  events: {
    invalidateKeys: [['events']] as const,
  },
  fighters: {
    invalidateKeys: [['fighters']] as const,
    refetchKeys: [['fighters', 'list']] as const,
  },
  rankings: {
    invalidateKeys: [['rankings']] as const,
  },
  predictions: {
    invalidateKeys: [['predictions', 'dashboard'], ['predictions', 'upcoming']] as const,
  },
  recommendations: {
    invalidateKeys: [['recommendations']] as const,
  },
  search: {
    // No caching for search — just refetch current query
    invalidateKeys: [['search']] as const,
  },
  watchlist: {
    invalidateKeys: [['watchlist']] as const,
    refetchKeys: [['watchlist', 'list']] as const,
  },
  notifications: {
    invalidateKeys: [['notifications', 'list'], ['notifications', 'count']] as const,
  },
  profile: {
    invalidateKeys: [['profile']] as const,
  },
} as const;
