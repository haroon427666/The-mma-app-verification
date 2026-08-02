/** Analytics — README + index */
/* 
## Analytics & Telemetry Platform

### Tracked Events (40+)
- App: startup, shutdown, foreground, background, crash
- Screen: view, duration
- Feature: search, fighter_view, event_view, prediction_view, ranking_view, etc.
- API: duration, error, retry
- Performance: render, FPS, memory
- Auth: login, logout, register
- Engagement: notification_received, recommendation_like

### Hooks
- `useAnalytics()` → track, sessionId, setUser
- `useScreenTracking(name)` → auto-track views
- `useEventTracking()` → track any event
- `usePerformanceTracking()` → API duration, render, FPS, errors
- `useFunnel(name)` → step tracking

### Usage
```tsx
function FighterScreen({ fighterId }) {
  useScreenTracking('FighterProfile');
  const { track } = useAnalytics();
  useEffect(() => { track('fighter_view', 'feature', { fighterId }); }, [fighterId]);
}
```
*/

export { AnalyticsProvider, AnalyticsManager, analyticsManager, screenTracker, performanceTracker, errorTracker, funnelTracker, experimentTracker, engagementTracker, useAnalyticsStore } from './AnalyticsManager';
export { useAnalytics, useScreenTracking, useEventTracking, usePerformanceTracking, useFunnel } from './AnalyticsHooks';
export { analyticsConfig, ANALYTICS_CONSTANTS, AnalyticsLogger, analyticsLogger, analyticsUtils } from './AnalyticsTypes';
export type { AnalyticsEventName, AnalyticsEventCategory, AnalyticsEvent, AnalyticsConfig, UserProperties, ScreenView, FunnelStep, Experiment } from './AnalyticsTypes';
export { AnalyticsError, UploadError, QueueError, ConfigurationError } from './AnalyticsTypes';
