/** API Endpoints — centralized endpoint constants */
export const API_ENDPOINTS = {
  // Auth
  AUTH: { LOGIN: '/v1/auth/login', REGISTER: '/v1/auth/register', REFRESH: '/v1/auth/refresh', LOGOUT: '/v1/auth/logout', ME: '/v1/me' },
  // Events
  EVENTS: { LIST: '/v1/events', DETAIL: (id: string) => `/v1/events/${id}`, FIGHT_CARD: (id: string) => `/v1/events/${id}/fights`, LIVE: (id: string) => `/v1/events/${id}/live` },
  // Fighters
  FIGHTERS: { LIST: '/v1/fighters', DETAIL: (id: string) => `/v1/fighters/${id}`, STATS: (id: string) => `/v1/fighters/${id}/stats`, COMPARE: '/v1/fighters/compare', SEARCH: '/v1/fighters/search' },
  // Rankings
  RANKINGS: { P4P: '/v1/rankings/p4p', DIVISION: (d: string) => `/v1/rankings/division/${d}`, HISTORY: (id: string) => `/v1/rankings/history/${id}`, GOAT: '/v1/rankings/goat', PROSPECTS: '/v1/rankings/prospects' },
  // Predictions
  PREDICTIONS: { FIGHT: (id: string) => `/v1/predictions/fight/${id}`, DASHBOARD: '/v1/predictions/dashboard', HISTORY: '/v1/predictions/history', ACCURACY: '/v1/predictions/accuracy', SAVE: (id: string) => `/v1/predictions/saved/${id}` },
  // Recommendations
  RECS: { FOR_YOU: '/v1/recommendations', TRENDING: '/v1/recommendations/trending', FEEDBACK: '/v1/recommendations/feedback' },
  // Search
  SEARCH: { QUERY: '/v1/search', AUTOCOMPLETE: '/v1/search/autocomplete', TRENDING: '/v1/search/trending' },
  // Watchlist
  WATCHLIST: { LIST: (t: string) => `/v1/watchlist/${t}`, ADD: (t: string, id: string) => `/v1/watchlist/${t}/${id}`, REMOVE: (t: string, id: string) => `/v1/watchlist/${t}/${id}`, REMINDERS: '/v1/watchlist/reminders' },
  // Notifications
  NOTIFICATIONS: { LIST: '/v1/notifications', MARK_READ: (id: string) => `/v1/notifications/${id}/read`, MARK_ALL: '/v1/notifications/read-all', PREFERENCES: '/v1/notifications/preferences' },
  // System
  SYSTEM: { HEALTH: '/v1/health', METRICS: '/v1/metrics', REMOTE_CONFIG: '/v1/remote-config' },
} as const;
