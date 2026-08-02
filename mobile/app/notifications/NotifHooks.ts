/** Notifications Hooks — useNotifications, usePushToken, useReminder, useNotificationSettings, useBadge */
import { useState, useCallback } from 'react';
import { useNotifStore, notifManager, pushService, localNotifs, reminderScheduler, permissionsHandler, notifRouter } from './NotifManager';
import type { NotifPreferences, NotificationType, ScheduledReminder } from './NotifTypes';

export function useNotifications() {
  const { pending, scheduled, history, badgeCount, permission } = useNotifStore();
  return { pending, scheduled, history, badgeCount, permission, dismiss: notifManager.dismiss.bind(notifManager), clearAll: () => useNotifStore.setState({ pending: [] }) };
}

export function usePushToken() {
  const { pushToken } = useNotifStore();
  const [loading, setLoading] = useState(false);
  const register = useCallback(async () => { setLoading(true); try { return await pushService.register(); } finally { setLoading(false); } }, []);
  const unregister = useCallback(async () => { await pushService.unregister(); }, []);
  return { pushToken, register, unregister, loading };
}

export function useReminder() {
  const [loading, setLoading] = useState(false);
  const schedule = useCallback(async (reminder: { type: NotificationType; title: string; body: string; triggerAt: number; routeId?: string; route?: any }) => {
    setLoading(true); try { return await localNotifs.schedule(reminder as any); } finally { setLoading(false); }
  }, []);
  const cancel = useCallback(async (id: string) => { await localNotifs.cancel(id); }, []);
  return { schedule, cancel, cancelAll: localNotifs.cancelAll.bind(localNotifs), loading };
}

export function useNotificationPermissions() {
  const { permission } = useNotifStore();
  const [loading, setLoading] = useState(false);
  const request = useCallback(async () => { setLoading(true); try { return await permissionsHandler.request(); } finally { setLoading(false); } }, []);
  return { permission, request, loading, isGranted: permission === 'granted' };
}

export function useNotificationSettings() {
  const { preferences } = useNotifStore();
  const update = useCallback((p: Partial<NotifPreferences>) => notifManager.updatePreferences(p), []);
  const toggleChannel = useCallback((c: string, v: boolean) => { notifManager.updatePreferences({ channels: { ...useNotifStore.getState().preferences.channels, [c]: v } }); }, []);
  return { preferences, update, toggleChannel };
}

export function useBadge() {
  const { badgeCount } = useNotifStore();
  return { badgeCount, setBadge: notifManager.updateBadge.bind(notifManager), clearBadge: notifManager.clearBadge.bind(notifManager) };
}
