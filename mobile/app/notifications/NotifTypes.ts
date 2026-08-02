/** Notifications Platform — all types, config, constants, errors, logger, events, utils */
export type NotificationType = 'fight_reminder' | 'event_reminder' | 'watchlist' | 'prediction' | 'ranking' | 'recommendation' | 'news' | 'system';
export type NotificationChannel = 'events' | 'fights' | 'rankings' | 'predictions' | 'recommendations' | 'marketing' | 'system';
export type NotificationAction = 'open' | 'dismiss' | 'snooze' | 'share' | 'custom';
export type PermissionStatus = 'granted' | 'denied' | 'undetermined' | 'provisional';
export type NotificationRoute = 'event' | 'fight' | 'fighter' | 'rankings' | 'prediction' | 'watchlist' | 'recommendations' | 'profile' | 'settings' | 'home';

export interface NotifConfig { enablePush: boolean; enableLocal: boolean; enableBadge: boolean; defaultSound: boolean; defaultVibration: boolean; reminderBufferMinutes: number; maxScheduledReminders: number; }
export interface PushPayload { id: string; type: NotificationType; title: string; body: string; route?: NotificationRoute; routeId?: string; imageUrl?: string; badge?: number; category?: string; data?: Record<string, string>; }
export interface ScheduledReminder { id: string; type: NotificationType; title: string; body: string; triggerAt: number; repeat?: 'daily' | 'weekly' | 'never'; route?: NotificationRoute; routeId?: string; }
export interface NotifPreferences { channels: Record<NotificationChannel, boolean>; quietHours: { enabled: boolean; start: string; end: string }; sound: boolean; vibration: boolean; preview: boolean; }
export interface NotifHistoryEntry { id: string; payload: PushPayload; receivedAt: number; openedAt?: number; dismissedAt?: number; actionTapped?: NotificationAction; }

export class NotificationError extends Error { constructor(m: string) { super(m); this.name = 'NotificationError'; } }
export class PermissionError extends NotificationError { constructor() { super('Notification permission denied'); this.name = 'PermissionError'; } }
export class PushRegistrationError extends NotificationError { constructor(m: string) { super(m); this.name = 'PushRegistrationError'; } }
export class SchedulingError extends NotificationError { constructor(m: string) { super(m); this.name = 'SchedulingError'; } }
export class RoutingError extends NotificationError { constructor(m: string) { super(m); this.name = 'RoutingError'; } }

export const defaultNotifConfig: NotifConfig = { enablePush: true, enableLocal: true, enableBadge: true, defaultSound: true, defaultVibration: true, reminderBufferMinutes: 30, maxScheduledReminders: 50 };
let _o: Partial<NotifConfig> = {};
export const notifConfig = { get: (): NotifConfig => ({ ...defaultNotifConfig, ..._o }), update: (p: Partial<NotifConfig>) => { _o = { ..._o, ...p }; } };

export const NOTIF_CONSTANTS = {
  CHANNELS: { EVENTS: 'events', FIGHTS: 'fights', RANKINGS: 'rankings', PREDICTIONS: 'predictions', RECS: 'recommendations', MARKETING: 'marketing', SYSTEM: 'system' } as const,
  ROUTE_MAP: { event: 'EventDetail', fight: 'FightDetail', fighter: 'FighterProfile', rankings: 'Rankings', prediction: 'Prediction', watchlist: 'Watchlist', recommendations: 'Recommendations', profile: 'Profile', settings: 'Settings', home: 'Home' } as const,
  DEFAULT_PREFS: { channels: { events: true, fights: true, rankings: true, predictions: true, recommendations: true, marketing: false, system: true }, quietHours: { enabled: false, start: '22:00', end: '08:00' }, sound: true, vibration: true, preview: true } as NotifPreferences,
};
export class NotifLogger { private p = '[Notifs]'; info(m: string) { console.log(`${this.p} ${m}`); } warn(m: string) { console.warn(`${this.p} ${m}`); } error(m: string, e?: Error) { console.error(`${this.p} ${m}`, e?.message ?? ''); } }
export const notifLogger = new NotifLogger();
class NotifEventBus { private h = new Set<(e: any) => void>(); on(h: (e: any) => void): () => void { this.h.add(h); return () => this.h.delete(h); } emit(e: any): void { this.h.forEach((f) => { try { f(e); } catch {} }); } }
export const notifEvents = new NotifEventBus();
export const notifUtils = { generateId: (): string => `notif-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, isQuietHours: (prefs: NotifPreferences, now?: Date): boolean => { if (!prefs.quietHours.enabled) return false; const d = now || new Date(); const [sh, sm] = prefs.quietHours.start.split(':').map(Number); const [eh, em] = prefs.quietHours.end.split(':').map(Number); const start = sh * 60 + sm; const end = eh * 60 + em; const current = d.getHours() * 60 + d.getMinutes(); return end < start ? current >= start || current < end : current >= start && current < end; } };