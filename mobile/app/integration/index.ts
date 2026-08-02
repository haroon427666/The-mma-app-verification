/** Production Integration — Offline strategy, cache invalidation, infinite pagination.

Single import surface for every feature module.
Usage: import { useInfinite, offline, cache, invalidate } from '@/app/integration';
*/

import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';

// ═══════════════════════════════════════════════════════════════════════════
// OFFLINE STRATEGY — per-feature cache + sync configuration
// ═══════════════════════════════════════════════════════════════════════════

export type OfflineMode = 'offline_first' | 'online_required' | 'cache_only';

export interface OfflineStrategy {
  mode: OfflineMode;
  staleTimeMs: number;
  gcTimeMs: number;
  backgroundRefresh: boolean;
  persistToMMKV: boolean;
  retryOnReconnect: boolean;
}

/** Offline strategy per feature — one source of truth for cache duration */
export const offline: Record<string, OfflineStrategy> = {
  events_live:   { mode: 'online_required', staleTimeMs: 30_000, gcTimeMs: 60_000, backgroundRefresh: true, persistToMMKV: false, retryOnReconnect: true },
  events_upcoming: { mode: 'offline_first', staleTimeMs: 300_000, gcTimeMs: 600_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  events_past:   { mode: 'offline_first', staleTimeMs: 3_600_000, gcTimeMs: 86_400_000, backgroundRefresh: false, persistToMMKV: true, retryOnReconnect: false },
  fighters:      { mode: 'offline_first', staleTimeMs: 600_000, gcTimeMs: 1_800_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  fighter_detail: { mode: 'offline_first', staleTimeMs: 300_000, gcTimeMs: 1_800_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  rankings:      { mode: 'offline_first', staleTimeMs: 600_000, gcTimeMs: 3_600_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  predictions:   { mode: 'online_required', staleTimeMs: 300_000, gcTimeMs: 600_000, backgroundRefresh: false, persistToMMKV: false, retryOnReconnect: true },
  recommendations: { mode: 'online_required', staleTimeMs: 300_000, gcTimeMs: 600_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  search:        { mode: 'online_required', staleTimeMs: 30_000, gcTimeMs: 120_000, backgroundRefresh: false, persistToMMKV: false, retryOnReconnect: false },
  watchlist:     { mode: 'offline_first', staleTimeMs: 300_000, gcTimeMs: 1_800_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  notifications: { mode: 'offline_first', staleTimeMs: 60_000, gcTimeMs: 300_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
  profile:       { mode: 'offline_first', staleTimeMs: 600_000, gcTimeMs: 3_600_000, backgroundRefresh: false, persistToMMKV: true, retryOnReconnect: false },
  home:          { mode: 'offline_first', staleTimeMs: 120_000, gcTimeMs: 600_000, backgroundRefresh: true, persistToMMKV: true, retryOnReconnect: true },
};

// ═══════════════════════════════════════════════════════════════════════════
// CACHE INVALIDATION MAP — mutation → affected query keys
// ═══════════════════════════════════════════════════════════════════════════

export const invalidate = {
  /** After any fighter favorite mutation, invalidate these */
  fighterFavoriteToggled: (queryClient: ReturnType<typeof useQueryClient>) => {
    queryClient.invalidateQueries({ queryKey: ['fighters', 'favorites'] });
    queryClient.invalidateQueries({ queryKey: ['fighter', 'detail'] });
    queryClient.invalidateQueries({ queryKey: ['watchlist', 'fighters'] });
    queryClient.invalidateQueries({ queryKey: ['home'] });
  },

  /** After event watchlist mutation */
  eventWatchlistToggled: (queryClient: ReturnType<typeof useQueryClient>) => {
    queryClient.invalidateQueries({ queryKey: ['events', 'watchlist'] });
    queryClient.invalidateQueries({ queryKey: ['watchlist', 'events'] });
    queryClient.invalidateQueries({ queryKey: ['home'] });
  },

  /** After notification mark-read */
  notificationReadChanged: (queryClient: ReturnType<typeof useQueryClient>) => {
    queryClient.invalidateQueries({ queryKey: ['notifications', 'list'] });
    queryClient.invalidateQueries({ queryKey: ['notifications', 'count'] });
  },

  /** After ranking sync completes */
  rankingsSynced: (queryClient: ReturnType<typeof useQueryClient>) => {
    queryClient.invalidateQueries({ queryKey: ['rankings'] });
  },

  /** After prediction viewed */
  predictionViewed: (queryClient: ReturnType<typeof useQueryClient>) => {
    queryClient.invalidateQueries({ queryKey: ['predictions', 'history'] });
  },

  /** Profile updated — invalidate all user-specific data */
  profileUpdated: (queryClient: ReturnType<typeof useQueryClient>) => {
    queryClient.invalidateQueries({ queryKey: ['profile'] });
    queryClient.invalidateQueries({ queryKey: ['preferences'] });
    queryClient.invalidateQueries({ queryKey: ['sessions'] });
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// INFINITE PAGINATION — production useInfiniteQuery wrapper
// ═══════════════════════════════════════════════════════════════════════════

interface PageParam { page?: number; cursor?: string; offset?: number; }

interface InfiniteConfig<TData, TParam extends PageParam> {
  queryKey: readonly unknown[];
  queryFn: (param: TParam) => Promise<{ items: TData[]; nextCursor?: string | null; nextPage?: number | null; total: number }>;
  initialParam: TParam;
  getNextParam: (lastResult: { items: TData[]; nextCursor?: string | null; nextPage?: number | null; total: number }, allResults: TData[]) => TParam | undefined;
  enabled?: boolean;
  staleTimeMs?: number;
  gcTimeMs?: number;
}

/** Production infinite scroll hook — cursor or offset-based, deduplicates, preserves order */
export function useInfinite<TData, TParam extends PageParam>(config: InfiniteConfig<TData, TParam>) {
  const seen = new Set<string>();

  return useInfiniteQuery({
    queryKey: config.queryKey,
    queryFn: async ({ pageParam }) => {
      const result = await config.queryFn(pageParam as TParam);
      return result;
    },
    initialPageParam: config.initialParam as any,
    getNextPageParam: (lastResult: any, allResults: any[]) => {
      const allItems = allResults.flatMap((r: any) => r?.items ?? []);
      return config.getNextParam(lastResult, allItems);
    },
    enabled: config.enabled ?? true,
    staleTime: config.staleTimeMs ?? 120_000,
    gcTime: config.gcTimeMs ?? 600_000,
    select: (data: any) => {
      // Deduplicate across all pages
      const allItems = data.pages.flatMap((p: any) => p?.items ?? []);
      const unique = allItems.filter((item: TData & { id?: string }) => {
        const key = (item as any).id ?? JSON.stringify(item);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      return { ...data, allItems: unique };
    },
    structuralSharing: true,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  });
}

/** Simple offset pagination — for lists that don't need cursor-based */
export function useOffsetPagination<TData>(
  queryKey: readonly unknown[],
  queryFn: (offset: number, limit: number) => Promise<{ items: TData[]; total: number }>,
  limit: number = 50,
  options?: { enabled?: boolean; staleTimeMs?: number; },
) {
  return useInfiniteQuery({
    queryKey: [...queryKey, 'paginated'],
    queryFn: ({ pageParam = 0 }) => queryFn(pageParam as number, limit),
    initialPageParam: 0,
    getNextPageParam: (lastResult: any, allResults: any[]) => {
      const totalLoaded = allResults.reduce((sum: number, r: any) => sum + (r?.items?.length ?? 0), 0);
      return totalLoaded < (lastResult?.total ?? 0) ? (allResults.length * limit) : undefined;
    },
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTimeMs ?? 120_000,
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// REACT QUERY CACHE CONFIG — default stale/gc times + retry policy
// ═══════════════════════════════════════════════════════════════════════════

export const cache = {
  /** Default stale times per entity type */
  stale: {
    live: 30_000,
    upcoming: 300_000,
    past: 3_600_000,
    fighter: 600_000,
    fighterDetail: 300_000,
    rankings: 600_000,
    predictions: 300_000,
    recommendations: 300_000,
    search: 30_000,
    watchlist: 300_000,
    notifications: 60_000,
    profile: 600_000,
  },
  /** GC times (how long inactive cache stays) */
  gc: {
    short: 120_000,
    medium: 600_000,
    long: 1_800_000,
    permanent: 3_600_000,
  },
};
