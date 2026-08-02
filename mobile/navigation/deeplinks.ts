/** Deep Link Navigation — production routing configuration.

  Wire this into your NavigationContainer linking config.
  Integrates with DeeplinkManager from app/deeplinks for universal link handling.

  Usage in RootNavigator:
    <NavigationContainer linking={deepLinkConfig}>
*/

import type { LinkingOptions, PathConfigMap } from '@react-navigation/native';

// ═══════════════════════════════════════════════════════════════════════════
// Route Map — mma:// scheme + https:// universal links
// ═══════════════════════════════════════════════════════════════════════════

export const deepLinkConfig: LinkingOptions<{}> = {
  prefixes: ['mma://', 'https://mma-app.com', 'https://app.mma.com'],
  config: {
    screens: {
      // Auth
      login: 'auth/login',
      register: 'auth/register',
      'forgot-password': 'auth/forgot',
      'reset-password': 'auth/reset',
      'verify-email': 'auth/verify',

      // Main tabs
      home: 'home',
      events: {
        screens: {
          list: 'events',
          detail: 'event/:id',
        },
      },
      fighters: {
        screens: {
          list: 'fighters',
          detail: 'fighter/:id',
          stats: 'fighter/:id/stats',
          compare: 'compare/:idA/:idB',
        },
      },
      rankings: {
        screens: {
          list: 'rankings',
          p4p: 'rankings/p4p',
          division: 'ranking/:division',
        },
      },
      predictions: {
        screens: {
          dashboard: 'predictions',
          detail: 'prediction/:id',
        },
      },
      search: 'search',
      watchlist: 'watchlist',
      notifications: 'notifications',
      profile: 'profile',
      settings: 'settings',
      recommendations: 'recommendation/:id',
    } satisfies PathConfigMap<{}>,
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// Deep Link Matrix — every supported route
// ═══════════════════════════════════════════════════════════════════════════

export const DEEP_LINK_MATRIX: Record<string, { route: string; params?: string[]; coldStart: boolean; background: boolean; auth?: boolean }> = {
  // Fighters
  'fighter/:id':          { route: 'fighters/detail',     params: ['id'], coldStart: true, background: true },
  'fighter/:id/stats':    { route: 'fighters/stats',      params: ['id'], coldStart: true, background: true },
  'compare/:idA/:idB':    { route: 'fighters/compare',    params: ['idA', 'idB'], coldStart: true, background: false },

  // Events
  'event/:id':            { route: 'events/detail',       params: ['id'], coldStart: true, background: true },
  'fight/:id':            { route: 'events/detail',       params: ['id'], coldStart: true, background: true },

  // Rankings
  'rankings':             { route: 'rankings/list',       coldStart: true, background: true },
  'rankings/p4p':         { route: 'rankings/p4p',        coldStart: true, background: true },
  'ranking/:division':    { route: 'rankings/division',   params: ['division'], coldStart: true, background: true },

  // Predictions
  'prediction/:id':       { route: 'predictions/detail',  params: ['id'], coldStart: true, background: true },

  // Recommendations
  'recommendation/:id':   { route: 'recommendations/item', params: ['id'], coldStart: true, background: false },

  // Search
  'search':               { route: 'search',              coldStart: true, background: true },
  'search?q=':            { route: 'search',              coldStart: true, background: true },

  // User
  'watchlist':            { route: 'watchlist',           coldStart: false, background: true, auth: true },
  'notifications':        { route: 'notifications',       coldStart: false, background: true, auth: true },
  'profile':              { route: 'profile',             coldStart: false, background: true, auth: true },
  'settings':             { route: 'settings',            coldStart: false, background: true, auth: true },
};

// ═══════════════════════════════════════════════════════════════════════════
// Navigation event handler — analytics + state restoration
// ═══════════════════════════════════════════════════════════════════════════

export function handleDeepLinkNavigation(url: string | null) {
  if (!url) return;

  // Log analytics
  try {
    const { track } = require('@/features/events/analytics/track');
    track('deepLinkOpened', url);
  } catch {
    // analytics optional
  }
}

/** Build a shareable deep link for any entity */
export function buildDeepLink(entityType: string, id: string): string {
  return `mma://${entityType}/${id}`;
}

/** Build a shareable universal link */
export function buildUniversalLink(entityType: string, id: string): string {
  return `https://mma-app.com/${entityType}/${id}`;
}
