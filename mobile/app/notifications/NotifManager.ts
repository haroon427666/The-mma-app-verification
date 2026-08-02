/** Notifications — Store, Provider, Manager, Push, Local, Routing */
import React, { createContext, useContext, useEffect, useMemo } from 'react';
import { create } from 'zustand';
import type { NotificationType, NotificationChannel, PermissionStatus, PushPayload, ScheduledReminder, NotifPreferences, NotifHistoryEntry, NotificationAction, NotificationRoute } from './NotifTypes';
import { notifConfig, notifLogger, notifEvents, notifUtils, NOTIF_CONSTANTS, NotificationError, PushRegistrationError, SchedulingError } from './NotifTypes';

// ── Store ──
interface NotifStore { permission: PermissionStatus; pushToken: string | null; badgeCount: number; preferences: NotifPreferences; pending: PushPayload[]; scheduled: ScheduledReminder[]; history: NotifHistoryEntry[]; }
export const useNotifStore = create<NotifStore>(() => ({ permission: 'undetermined', pushToken: null, badgeCount: 0, preferences: NOTIF_CONSTANTS.DEFAULT_PREFS, pending: [], scheduled: [], history: [] }));

// ── Provider ──
const NotifContext = createContext<{ permission: PermissionStatus; badgeCount: number; }>({ permission: 'undetermined', badgeCount: 0 });
export function NotifProvider({ children }: { children: React.ReactNode }) {
  const { permission, badgeCount } = useNotifStore();
  const value = useMemo(() => ({ permission, badgeCount }), [permission, badgeCount]);
  return <NotifContext.Provider value={value}>{children}</NotifContext.Provider>;
}

// ── Permissions ──
class PermissionsHandler {
  async check(): Promise<PermissionStatus> { useNotifStore.setState({ permission: 'granted' }); return 'granted'; }
  async request(): Promise<PermissionStatus> { useNotifStore.setState({ permission: 'granted' }); return 'granted'; }
}
export const permissionsHandler = new PermissionsHandler();

// ── Push Registration ──
class PushRegistrationService { private token: string | null = null;
  async register(): Promise<string> { try { this.token = `push-token-${Date.now()}`; useNotifStore.setState({ pushToken: this.token }); notifLogger.info('Push registered'); return this.token; } catch (e) { throw new PushRegistrationError((e as Error).message); } }
  async unregister(): Promise<void> { this.token = null; useNotifStore.setState({ pushToken: null }); notifLogger.info('Push unregistered'); }
  getToken(): string | null { return this.token; }
}
export const pushService = new PushRegistrationService();

// ── Local Notifications ──
class LocalNotifService {
  async schedule(reminder: Omit<ScheduledReminder, 'id'>): Promise<ScheduledReminder> {
    const cfg = notifConfig.get();
    const scheduled = useNotifStore.getState().scheduled;
    if (scheduled.length >= cfg.maxScheduledReminders) throw new SchedulingError('Max reminders reached');
    const r: ScheduledReminder = { ...reminder, id: notifUtils.generateId() };
    useNotifStore.setState({ scheduled: [...scheduled, r] });
    notifLogger.info(`Scheduled: ${r.title}`);
    return r;
  }
  async cancel(id: string): Promise<void> { useNotifStore.setState({ scheduled: useNotifStore.getState().scheduled.filter((r) => r.id !== id) }); }
  async cancelAll(): Promise<void> { useNotifStore.setState({ scheduled: [] }); }
  async reschedule(id: string, newTriggerAt: number): Promise<void> { useNotifStore.setState({ scheduled: useNotifStore.getState().scheduled.map((r) => r.id === id ? { ...r, triggerAt: newTriggerAt } : r) }); }
}
export const localNotifs = new LocalNotifService();

// ── Reminder Scheduler ──
class ReminderScheduler {
  async scheduleFightReminder(fightId: string, title: string, body: string, triggerAt: number): Promise<ScheduledReminder> {
    return localNotifs.schedule({ type: 'fight_reminder', title, body, triggerAt, route: 'fight', routeId: fightId });
  }
  async scheduleEventReminder(eventId: string, title: string, body: string, triggerAt: number): Promise<ScheduledReminder> {
    return localNotifs.schedule({ type: 'event_reminder', title, body, triggerAt, route: 'event', routeId: eventId });
  }
}
export const reminderScheduler = new ReminderScheduler();

// ── Routing ──
class NotifRouter {
  route(payload: PushPayload): { screen: string; params?: any } {
    const route = payload.route || 'home';
    const screen = (NOTIF_CONSTANTS.ROUTE_MAP as any)[route] || 'Home';
    const params = payload.routeId ? { id: payload.routeId } : undefined;
    return { screen, params };
  }
}
export const notifRouter = new NotifRouter();

// ── Manager ──
export class NotifManager {
  private log = notifLogger;

  async initialize(): Promise<void> { await permissionsHandler.check(); await pushService.register(); this.log.info('NotifManager initialized'); }

  handlePush(payload: PushPayload): void {
    const store = useNotifStore.getState();
    useNotifStore.setState({ pending: [...store.pending, payload], badgeCount: store.badgeCount + 1, history: [...store.history, { id: payload.id, payload, receivedAt: Date.now() }] });
    notifEvents.emit({ type: 'received', payload });
  }

  updateBadge(count: number): void { useNotifStore.setState({ badgeCount: count }); }
  clearBadge(): void { useNotifStore.setState({ badgeCount: 0 }); }

  updatePreferences(prefs: Partial<NotifPreferences>): void {
    useNotifStore.setState({ preferences: { ...useNotifStore.getState().preferences, ...prefs } });
  }

  async dismiss(id: string): Promise<void> {
    useNotifStore.setState({ pending: useNotifStore.getState().pending.filter((n) => n.id !== id) });
  }
}
export const notifManager = new NotifManager();

// ── Notification History ──
class NotifHistory {
  private maxEntries = 100;
  get(): NotifHistoryEntry[] { return useNotifStore.getState().history; }
  add(entry: NotifHistoryEntry): void { const h = [entry, ...useNotifStore.getState().history].slice(0, this.maxEntries); useNotifStore.setState({ history: h }); }
  clear(): void { useNotifStore.setState({ history: [] }); }
}
export const notifHistory = new NotifHistory();

// ── Analytics ──
class NotifAnalytics {
  trackReceived(type: NotificationType): void {}
  trackOpened(type: NotificationType): void {}
  trackDismissed(type: NotificationType): void {}
  trackAction(type: NotificationType, action: NotificationAction): void {}
  trackPermission(status: PermissionStatus): void {}
}
export const notifAnalytics = new NotifAnalytics();