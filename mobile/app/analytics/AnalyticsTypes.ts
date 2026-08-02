/** Analytics Platform — all types, config, constants, errors, logger, utils */
export type AnalyticsEventName =
  | 'app_startup' | 'app_shutdown' | 'app_foreground' | 'app_background' | 'app_crash'
  | 'screen_view' | 'screen_duration'
  | 'search' | 'search_result_tap'
  | 'fighter_view' | 'fighter_favorite' | 'fighter_compare'
  | 'event_view' | 'event_watchlist_add'
  | 'prediction_view' | 'prediction_save' | 'prediction_share'
  | 'recommendation_view' | 'recommendation_like' | 'recommendation_dismiss'
  | 'notification_received' | 'notification_opened'
  | 'ranking_view' | 'watchlist_view'
  | 'login' | 'logout' | 'register' | 'session_restore'
  | 'api_duration' | 'api_error' | 'api_retry'
  | 'performance_render' | 'performance_fps' | 'performance_memory'
  | 'error_boundary' | 'error_unhandled';

export type AnalyticsEventCategory = 'app' | 'screen' | 'user' | 'feature' | 'api' | 'performance' | 'error';

export interface AnalyticsEvent {
  name: AnalyticsEventName; category: AnalyticsEventCategory; properties?: Record<string, any>; timestamp: number; sessionId: string; userId?: string;
}

export interface AnalyticsConfig { enabled: boolean; batchSize: number; uploadIntervalMs: number; maxQueueSize: number; samplingRate: number; anonymizeIP: boolean; }
export interface UserProperties { userId?: string; favoriteFighters?: string[]; favoriteWeightClasses?: string[]; themeMode?: string; language?: string; platform?: string; appVersion?: string; }
export interface ScreenView { name: string; startTime: number; durationMs?: number; }
export interface FunnelStep { name: string; users: number; completed: number; droppedOff: number; conversionRate: number; }
export interface Experiment { id: string; name: string; variant: string; controlGroup: boolean; }

export class AnalyticsError extends Error { constructor(m: string) { super(m); this.name = 'AnalyticsError'; } }
export class UploadError extends AnalyticsError { constructor(m: string) { super(m); this.name = 'UploadError'; } }
export class QueueError extends AnalyticsError { constructor(m: string) { super(m); this.name = 'QueueError'; } }
export class ConfigurationError extends AnalyticsError { constructor(m: string) { super(m); this.name = 'ConfigurationError'; } }

export const defaultAnalyticsConfig: AnalyticsConfig = { enabled: true, batchSize: 20, uploadIntervalMs: 30000, maxQueueSize: 500, samplingRate: 1.0, anonymizeIP: true };
const _ac: Partial<AnalyticsConfig> = {};
export const analyticsConfig = { get: (): AnalyticsConfig => ({ ...defaultAnalyticsConfig, ..._ac }), update: (p: Partial<AnalyticsConfig>) => { Object.assign(_ac, p); } };

export const ANALYTICS_CONSTANTS = {
  DIMENSIONS: { SCREEN: 'screen_name', EVENT_TYPE: 'event_type', FEATURE: 'feature_module', SOURCE: 'traffic_source', PLATFORM: 'platform' },
  METRICS: { COUNT: 'event_count', DURATION: 'duration_ms', VALUE: 'value', RATE: 'rate' },
} as const;

export class AnalyticsLogger { private p = '[Analytics]'; info(m: string) { console.log(`${this.p} ${m}`); } warn(m: string) { console.warn(`${this.p} ${m}`); } error(m: string) { console.error(`${this.p} ${m}`); } }
export const analyticsLogger = new AnalyticsLogger();
export const analyticsUtils = { generateSessionId: (): string => `analytics-sess-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, isSampled: (rate: number): boolean => Math.random() < rate, anonymize: (ip: string): string => ip.split('.').slice(0, 3).join('.') + '.0' };