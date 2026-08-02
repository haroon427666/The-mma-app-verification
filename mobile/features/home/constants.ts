/** Home feature — constants */

export const HOME_REFRESH_INTERVAL = 30_000;
export const HOME_STALE_TIME = 2 * 60 * 1000;
export const MAX_LIVE_EVENTS = 5;
export const MAX_UPCOMING_EVENTS = 5;
export const MAX_TRENDING_FIGHTERS = 8;
export const SECTIONS = [
  'live', 'upcoming', 'recommended', 'trending',
  'titleFights', 'predictions', 'rankings',
] as const;
