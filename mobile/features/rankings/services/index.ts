/** Rankings services — query keys, cache, analytics, deeplinks */

export const rankingKeys = {
  all: ['rankings'] as const,
  p4p: () => [...rankingKeys.all, 'p4p'] as const,
  division: (d: string) => [...rankingKeys.all, 'division', d] as const,
  history: (fighterId: string) => [...rankingKeys.all, 'history', fighterId] as const,
  goat: () => [...rankingKeys.all, 'goat'] as const,
  prospects: (d?: string) => [...rankingKeys.all, 'prospects', d] as const,
  movement: () => [...rankingKeys.all, 'movement'] as const,
  streaks: () => [...rankingKeys.all, 'streaks'] as const,
  champions: () => [...rankingKeys.all, 'champions'] as const,
  championsHistory: (wc?: string) => [...rankingKeys.all, 'championsHistory', wc] as const,
  titleDefenses: () => [...rankingKeys.all, 'titleDefenses'] as const,
  elo: () => [...rankingKeys.all, 'elo'] as const,
  composite: () => [...rankingKeys.all, 'composite'] as const,
};

export const rankingCache = {
  staleTime: 10 * 60 * 1000,
  liveStaleTime: 60 * 1000,
  gcTime: 24 * 60 * 60 * 1000,
};

export const rankingAnalytics = {
  p4pViewed: () => { if (__DEV__) console.log('[analytics] p4p_viewed'); },
  divisionViewed: (d: string) => { if (__DEV__) console.log('[analytics] division_viewed', { d }); },
  goatViewed: () => { if (__DEV__) console.log('[analytics] goat_viewed'); },
  prospectsViewed: () => { if (__DEV__) console.log('[analytics] prospects_viewed'); },
  fighterOpened: (id: string) => { if (__DEV__) console.log('[analytics] ranking_fighter_opened', { id }); },
  historyViewed: (id: string) => { if (__DEV__) console.log('[analytics] ranking_history_viewed', { id }); },
  compareUsed: () => { if (__DEV__) console.log('[analytics] ranking_compare_used'); },
};

export const rankingDeeplinks = {
  p4p: 'mma://rankings/p4p',
  division: (d: string) => `mma://rankings/${encodeURIComponent(d)}`,
  goat: 'mma://rankings/goat',
  prospects: 'mma://rankings/prospects',
  fighter: (id: string) => `mma://rankings/history/${id}`,
};
