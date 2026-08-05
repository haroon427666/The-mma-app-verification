/** Analytics Hooks — useAnalytics, useScreenTracking, useEventTracking, usePerformanceTracking, useFunnel */
import { useEffect, useCallback, useRef } from 'react';
import { analyticsManager, screenTracker, performanceTracker, errorTracker, funnelTracker, experimentTracker, engagementTracker, useAnalyticsStore } from './AnalyticsManager';
import type { AnalyticsEventName, AnalyticsEventCategory } from './AnalyticsTypes';

export function useAnalytics() {
  const store = useAnalyticsStore();
  const track = useCallback((name: AnalyticsEventName, category: AnalyticsEventCategory = 'feature', properties?: Record<string, any>) => { analyticsManager.track(name, category, properties); }, []);
  return { track, sessionId: store.sessionId, enabled: store.enabled, setUser: analyticsManager.setUserProperties.bind(analyticsManager) };
}

export function useScreenTracking(screenName: string) {
  useEffect(() => { screenTracker.trackView(screenName); return () => screenTracker.trackDuration(); }, [screenName]);
}

export function useEventTracking() {
  const track = useCallback((name: AnalyticsEventName, category: AnalyticsEventCategory = 'feature', props?: Record<string, any>) => { analyticsManager.track(name, category, props); }, []);
  return { track };
}

export function usePerformanceTracking() {
  const trackAPI = useCallback((endpoint: string, durationMs: number) => { performanceTracker.trackAPIDuration(endpoint, durationMs); }, []);
  const trackRender = useCallback((screenName: string, durationMs: number) => { performanceTracker.trackRender(screenName, durationMs); }, []);
  const trackFPS = useCallback((fps: number) => { performanceTracker.trackFPS(fps); }, []);
  const trackError = useCallback((err: Error, ctx?: string) => { errorTracker.trackError(err, ctx); }, []);
  return { trackAPI, trackRender, trackFPS, trackError };
}

export function useFunnel(funnelName: string) {
  const funnelRef = useRef(funnelName);
  useEffect(() => { funnelTracker.start(funnelRef.current); return () => { funnelTracker.end(funnelRef.current); }; }, []);
  const step = useCallback((stepName: string, completed: boolean) => { funnelTracker.step(funnelRef.current, stepName, completed); }, []);
  return { step };
}
