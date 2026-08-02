/** NotificationProvider — push token registration + listeners */

import React, { useEffect, useRef } from 'react';
import { useAuthStore } from '@/stores/auth';
import { notificationService } from '@/services/notifications';
import type { PushNotificationData } from '@/types';
import type { NavigationContainerRef } from '@react-navigation/native';

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.status === 'authenticated');
  const notificationListener = useRef<any>();
  const responseListener = useRef<any>();

  useEffect(() => {
    if (isAuthenticated) {
      notificationService.register();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    notificationListener.current = notificationService.addNotificationListener(
      (data: PushNotificationData) => {
        // Update badge
        notificationService.getBadgeCount().then((count) => {
          notificationService.setBadgeCount(count);
        });
      },
    );

    responseListener.current = notificationService.addResponseListener(
      (response) => {
        const data = response.notification.request.content.data;
        // Navigation is handled by the root navigator
      },
    );

    return () => {
      notificationListener.current?.remove();
      responseListener.current?.remove();
    };
  }, []);

  return <>{children}</>;
}
