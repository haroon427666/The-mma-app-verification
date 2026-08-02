/** Notification service — push token registration, notification handling */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import api from './api';
import { useAuthStore } from '@/stores/auth';
import type { PushNotificationData } from '@/types';

// Configure how notifications appear when app is foregrounded
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
  }),
});

export const notificationService = {
  async register(): Promise<string | null> {
    if (!Device.isDevice) return null;

    const { status: existing } = await Notifications.getPermissionsAsync();
    let finalStatus = existing;

    if (existing !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') return null;

    const token = await Notifications.getExpoPushTokenAsync({
      projectId: process.env.EXPO_PROJECT_ID,
    });

    // Send token to backend
    const user = useAuthStore.getState().user;
    if (user) {
      try {
        await api.post('/v1/me/devices', {
          platform: Platform.OS,
          device_token: token.data,
        });
      } catch {
        // Non-blocking — retry on next app open
      }
    }

    return token.data;
  },

  async unregister(): Promise<void> {
    const token = await Notifications.getExpoPushTokenAsync();
    try {
      await api.delete(`/v1/me/devices/${token.data}`);
    } catch { /* fire-and-forget */ }
  },

  addNotificationListener(
    handler: (notification: PushNotificationData) => void,
  ) {
    return Notifications.addNotificationReceivedListener((notification) => {
      const data = notification.request.content.data as PushNotificationData;
      handler(data);
    });
  },

  addResponseListener(
    handler: (response: Notifications.NotificationResponse) => void,
  ) {
    return Notifications.addNotificationResponseReceivedListener(handler);
  },

  async getBadgeCount(): Promise<number> {
    try {
      const { data } = await api.get<{ count: number }>('/v1/notifications?read=false&limit=1');
      return data.count;
    } catch {
      return 0;
    }
  },

  async setBadgeCount(count: number): Promise<void> {
    await Notifications.setBadgeCountAsync(count);
  },
};
