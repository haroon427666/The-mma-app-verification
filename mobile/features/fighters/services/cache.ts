/** Fighters cache + socket + offline + analytics */

// Cache helpers
export const fighterCache = {
  staleTime: { list: 10 * 60000, detail: 10 * 60000, stats: 30 * 60000, history: 30 * 60000, similar: 60 * 60000 },
  gcTime: 24 * 60 * 60000,
};

// Offline queue
import { create } from 'zustand';

export const useFighterOfflineStore = create<{ pendingFavorites: Set<string> }>(() => ({ pendingFavorites: new Set() }));

// Analytics
export const fighterAnalytics = {
  profileViewed: (id: string, name: string) => { if (__DEV__) console.log('[analytics] fighter_profile_viewed', { id, name }); },
  statsViewed: (id: string) => { if (__DEV__) console.log('[analytics] fighter_stats_viewed', { id }); },
  compared: (a: string, b: string) => { if (__DEV__) console.log('[analytics] fighters_compared', { a, b }); },
  favorited: (id: string) => { if (__DEV__) console.log('[analytics] fighter_favorited', { id }); },
  unfavorited: (id: string) => { if (__DEV__) console.log('[analytics] fighter_unfavorited', { id }); },
  shared: (id: string) => { if (__DEV__) console.log('[analytics] fighter_shared', { id }); },
  similarViewed: (id: string) => { if (__DEV__) console.log('[analytics] similar_fighters_viewed', { id }); },
};
