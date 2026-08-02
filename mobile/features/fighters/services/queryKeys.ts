/** Fighters Query Keys — centralized, namespaced */

export const fighterKeys = {
  all: ['fighters'] as const,
  lists: () => [...fighterKeys.all, 'list'] as const,
  list: (filter?: string) => [...fighterKeys.lists(), filter] as const,
  details: () => [...fighterKeys.all, 'detail'] as const,
  detail: (id: string) => [...fighterKeys.details(), id] as const,
  search: (query: string) => [...fighterKeys.all, 'search', query] as const,
  trending: () => [...fighterKeys.all, 'trending'] as const,
  champions: (wc?: string) => [...fighterKeys.all, 'champions', wc] as const,
};

export const fighterStatsKeys = {
  all: (id: string) => [...fighterKeys.detail(id), 'stats'] as const,
  striking: (id: string) => [...fighterStatsKeys.all(id), 'striking'] as const,
  grappling: (id: string) => [...fighterStatsKeys.all(id), 'grappling'] as const,
};

export const fighterHistoryKeys = {
  all: (id: string) => [...fighterKeys.detail(id), 'fights'] as const,
  list: (id: string, result?: string) => [...fighterHistoryKeys.all(id), result] as const,
  timeline: (id: string) => [...fighterKeys.detail(id), 'timeline'] as const,
  achievements: (id: string) => [...fighterKeys.detail(id), 'achievements'] as const,
};

export const similarityKeys = {
  all: (id: string) => [...fighterKeys.detail(id), 'similar'] as const,
  breakdown: (a: string, b: string) => ['similarity', a, b] as const,
};

export const predictionKeys = {
  fighter: (id: string) => ['predictions', 'fighter', id] as const,
  matchup: (a: string, b: string) => ['predictions', 'matchup', a, b] as const,
};

export const favoriteKeys = {
  all: ['favorites', 'fighters'] as const,
  check: (id: string) => [...favoriteKeys.all, 'check', id] as const,
};
