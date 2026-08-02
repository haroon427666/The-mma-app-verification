/** Bootstrap hooks — useBootstrap, useStartup, useDependencies */
import { useEffect, useState } from 'react';
import { useBootstrapState } from './BootstrapState';
import { container } from './DependencyContainer';
import type { StartupStage, BootstrapMetrics } from './BootstrapTypes';

export function useBootstrap() {
  const { stage, isReady, progress, error, startupTimeMs } = useBootstrapState();
  return { stage, isReady, progress, error, startupTimeMs, loading: !isReady && stage !== 'failed' };
}

export function useStartup() { return useBootstrap(); }

export function useStartupStatus() {
  const { stage, error } = useBootstrapState();
  const [metrics, setMetrics] = useState<BootstrapMetrics | null>(null);
  useEffect(() => {
    if (stage === 'ready') {
      const state = useBootstrapState.getState();
      setMetrics({ coldStart: true, totalDurationMs: state.startupTimeMs, stageDurations: {}, providerCount: 0 });
    }
  }, [stage]);
  return { stage, error, metrics, isReady: stage === 'ready', isFailed: stage === 'failed' };
}

export function useInitialization() { return useBootstrap(); }

export function useDependencies() { return { container, resolve: <T>(token: symbol) => container.resolve<T>(token) }; }
