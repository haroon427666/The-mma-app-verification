/** Analytics — Store, Manager, Trackers (Event, Screen, Navigation, Performance, Error, Funnel, Experiment), Uploader */
import React, { useMemo } from 'react';
import { create } from 'zustand';
import type { AnalyticsEvent, AnalyticsEventName, AnalyticsEventCategory, UserProperties, ScreenView, FunnelStep, Experiment, AnalyticsConfig } from './AnalyticsTypes';
import { analyticsConfig, analyticsLogger, analyticsUtils, AnalyticsError } from './AnalyticsTypes';

// ── Store ──
interface Store { enabled: boolean; queuedEvents: number; uploadStatus: 'idle' | 'uploading' | 'error'; sessionId: string; userProps: UserProperties; screenViews: ScreenView[]; experiments: Experiment[]; }
export const useAnalyticsStore = create<Store>(() => ({ enabled: true, queuedEvents: 0, uploadStatus: 'idle', sessionId: analyticsUtils.generateSessionId(), userProps: {}, screenViews: [], experiments: [] }));

// ── Context ──
const AnalyticsContext = React.createContext<{ sessionId: string; enabled: boolean }>({ sessionId: '', enabled: false });
export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const val = useMemo(() => ({ sessionId: useAnalyticsStore.getState().sessionId, enabled: useAnalyticsStore.getState().enabled }), []);
  return <AnalyticsContext.Provider value={val}>{children}</AnalyticsContext.Provider>;
}

// ── Queue ──
class EventQueue { private events: AnalyticsEvent[] = []; private cfg = analyticsConfig;
  enqueue(event: AnalyticsEvent): void { if (this.events.length >= this.cfg.get().maxQueueSize) this.events.shift(); this.events.push(event); useAnalyticsStore.setState({ queuedEvents: this.events.length }); }
  getBatch(): AnalyticsEvent[] { const batch = this.events.splice(0, this.cfg.get().batchSize); useAnalyticsStore.setState({ queuedEvents: this.events.length }); return batch; }
  get size(): number { return this.events.length; }
}
const eventQueue = new EventQueue();

// ── Event Uploader ──
class EventUploader {
  private timer: any = null;
  start(): void { this.timer = setInterval(() => this.flush(), analyticsConfig.get().uploadIntervalMs); }
  async flush(): Promise<void> { const batch = eventQueue.getBatch(); if (batch.length === 0) return; useAnalyticsStore.setState({ uploadStatus: 'uploading' }); try { /* API upload */ useAnalyticsStore.setState({ uploadStatus: 'idle' }); } catch { useAnalyticsStore.setState({ uploadStatus: 'error' }); } }
  stop(): void { if (this.timer) { clearInterval(this.timer); } }
}
const uploader = new EventUploader();

// ── Manager ──
export class AnalyticsManager {
  private log = analyticsLogger;
  private sessionId = analyticsUtils.generateSessionId();

  track(name: AnalyticsEventName, category: AnalyticsEventCategory, properties?: Record<string, any>): void {
    if (!analyticsConfig.get().enabled) return;
    if (!analyticsUtils.isSampled(analyticsConfig.get().samplingRate)) return;
    const event: AnalyticsEvent = { name, category, properties, timestamp: Date.now(), sessionId: this.sessionId, userId: useAnalyticsStore.getState().userProps.userId };
    eventQueue.enqueue(event);
  }

  setUserProperties(props: UserProperties): void { useAnalyticsStore.setState({ userProps: { ...useAnalyticsStore.getState().userProps, ...props } }); }
  initialize(): void { this.track('app_startup', 'app'); uploader.start(); this.log.info('Analytics initialized'); }
}

// ── Specialized Trackers ──
class ScreenTracker {
  private currentScreen: ScreenView | null = null;
  trackView(name: string): void { this.currentScreen = { name, startTime: Date.now() }; analyticsManager.track('screen_view', 'screen', { screenName: name }); }
  trackDuration(): void { if (this.currentScreen) { this.currentScreen.durationMs = Date.now() - this.currentScreen.startTime; analyticsManager.track('screen_duration', 'screen', { screenName: this.currentScreen.name, durationMs: this.currentScreen.durationMs }); } }
}

class PerformanceTracker {
  trackAPIDuration(endpoint: string, durationMs: number): void { analyticsManager.track('api_duration', 'api', { endpoint, durationMs }); }
  trackRender(screenName: string, durationMs: number): void { analyticsManager.track('performance_render', 'performance', { screenName, durationMs }); }
  trackFPS(fps: number): void { analyticsManager.track('performance_fps', 'performance', { fps }); }
}

class ErrorTracker {
  trackError(error: Error, context?: string): void { analyticsManager.track('error_unhandled', 'error', { errorName: error.name, message: error.message, context }); }
  trackBoundary(error: Error, componentStack?: string): void { analyticsManager.track('error_boundary', 'error', { errorName: error.name, message: error.message, componentStack }); }
}

class FunnelTracker {
  private funnels = new Map<string, FunnelStep[]>();
  start(funnelName: string): void { this.funnels.set(funnelName, []); }
  step(funnelName: string, stepName: string, completed: boolean): void { const funnel = this.funnels.get(funnelName); if (funnel) funnel.push({ name: stepName, users: 1, completed: completed ? 1 : 0, droppedOff: completed ? 0 : 1, conversionRate: completed ? 1 : 0 }); }
  end(funnelName: string): FunnelStep[] { return this.funnels.get(funnelName) || []; }
}

class ExperimentTracker {
  private experiments = new Map<string, Experiment>();
  start(exp: Experiment): void { this.experiments.set(exp.id, exp); useAnalyticsStore.setState({ experiments: Array.from(this.experiments.values()) }); }
  trackConversion(experimentId: string, event: string): void { /* Track conversion for experiment */ }
}

class EngagementTracker {
  trackSession(durationMs: number): void { analyticsManager.track('app_shutdown', 'app', { durationMs }); }
  trackFeature(feature: string, action: string): void { analyticsManager.track(action as any, 'feature', { feature }); }
}

export const analyticsManager = new AnalyticsManager();
export const screenTracker = new ScreenTracker();
export const performanceTracker = new PerformanceTracker();
export const errorTracker = new ErrorTracker();
export const funnelTracker = new FunnelTracker();
export const experimentTracker = new ExperimentTracker();
export const engagementTracker = new EngagementTracker();
