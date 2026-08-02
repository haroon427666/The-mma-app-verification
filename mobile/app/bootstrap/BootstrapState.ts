/** Bootstrap state — Zustand store */
import { create } from 'zustand';
import type { BootstrapState, StartupStage } from './BootstrapTypes';

interface Store extends BootstrapState {
  setStage: (s: StartupStage) => void; setProgress: (p: number) => void;
  setReady: () => void; setError: (e: Error, stage: StartupStage) => void;
}
export const useBootstrapState = create<Store>((set) => ({
  stage: 'idle', progress: 0, isReady: false, error: null, startupTimeMs: 0, startedAt: 0,
  setStage: (stage) => set({ stage, progress: stageProgress(stage) }),
  setProgress: (progress) => set({ progress }),
  setReady: () => set({ stage: 'ready', isReady: true, progress: 100, startupTimeMs: Date.now() - (useBootstrapState.getState().startedAt || Date.now()) }),
  setError: (error, stage) => set({ error: new (await import('./BootstrapTypes')).BootstrapError(error.message, stage, stage !== 'auth'), stage: 'failed' }),
}));

const stageProgress = (s: StartupStage): number => ({ idle: 0, env: 10, storage: 20, theme_locale: 35, query_client: 50, auth: 65, notifications: 80, remote_config: 90, ready: 100, failed: 0 }[s] ?? 0);
