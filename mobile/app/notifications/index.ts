/** Notifications — README + index */
/* 
## Push Notifications Platform

### Architecture
```
AppBootstrap (Stage 6)
  → NotifManager.initialize()
  → Permissions.check/request
  → PushService.register()
  → NotifProvider wraps app
```

### Features
- Push notifications (remote)
- Local notifications (scheduled reminders)
- Per-channel preferences (7 channels)
- Quiet hours enforcement
- Notification routing to any screen
- Badge count management
- Notification history (last 100)

### Hooks
- `useNotifications()` → pending, history, badge, dismiss
- `usePushToken()` → register, unregister
- `useReminder()` → schedule, cancel  
- `useNotificationPermissions()` → check, request
- `useNotificationSettings()` → preferences, toggle channels
- `useBadge()` → badgeCount, set, clear
*/

export { NotifProvider, notifManager, NotifManager, pushService, localNotifs, reminderScheduler, notifRouter, permissionsHandler, notifHistory, notifAnalytics, useNotifStore } from './NotifManager';
export { useNotifications, usePushToken, useReminder, useNotificationPermissions, useNotificationSettings, useBadge } from './NotifHooks';
export { notifConfig, NOTIF_CONSTANTS, NotifLogger, notifLogger, notifEvents, notifUtils } from './NotifTypes';
export type { NotificationType, NotificationChannel, NotificationAction, PermissionStatus, NotificationRoute, NotifConfig, PushPayload, ScheduledReminder, NotifPreferences, NotifHistoryEntry } from './NotifTypes';
export { NotificationError, PermissionError, PushRegistrationError, SchedulingError, RoutingError } from './NotifTypes';
