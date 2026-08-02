/** Predictions Query Keys — centralized, namespaced factory functions */

export const predictionKeys = {
  all: ['predictions'] as const,
  fight: (fightId: string) => [...predictionKeys.all, 'fight', fightId] as const,
  event: (eventId: string) => [...predictionKeys.all, 'event', eventId] as const,
  dashboard: () => [...predictionKeys.all, 'dashboard'] as const,
  highlights: () => [...predictionKeys.all, 'highlights'] as const,
  history: (page = 1) => [...predictionKeys.all, 'history', page] as const,
  accuracy: () => [...predictionKeys.all, 'accuracy'] as const,
  matchup: (a: string, b: string) => [...predictionKeys.all, 'matchup', a, b] as const,
  monteCarlo: (fightId: string) => [...predictionKeys.all, 'monteCarlo', fightId] as const,
  factors: (fightId: string) => [...predictionKeys.all, 'factors', fightId] as const,
  odds: (fightId: string) => [...predictionKeys.all, 'odds', fightId] as const,
  saved: () => [...predictionKeys.all, 'saved'] as const,
};

export const predictionCache = {
  staleTime: 5 * 60 * 1000,
  liveStaleTime: 30 * 1000,
  historyStaleTime: 60 * 60 * 1000,
  accuracyStaleTime: 60 * 60 * 1000,
};
