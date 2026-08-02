/** Bootstrap constants */
export const BOOTSTRAP_CONSTANTS = {
  MIN_SPLASH_MS: 1500, MAX_STARTUP_MS: 15000,
  STAGE_COUNT: 8, PROGRESS_INCREMENT: 12.5,
  STORAGE_KEYS: { THEME: 'theme_pref', LOCALE: 'locale_pref', SESSION: 'session_token', FIRST_LAUNCH: 'first_launch' },
} as const;
