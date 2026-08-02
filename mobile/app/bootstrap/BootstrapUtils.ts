/** Bootstrap utilities */
import { BootstrapEvent } from './BootstrapTypes';
export function formatStartupTime(ms: number): string { return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`; }
export function isStageCritical(stage: string): boolean { return ['env', 'storage', 'query_client'].includes(stage); }
export function shouldRetryStartup(error: Error): boolean { return error.message?.includes('network') || error.message?.includes('timeout') || false; }
export function logBootstrapEvent(e: BootstrapEvent): void { if (__DEV__) console.log(`[Boot:${e.type}]`, e.stage || '', e.durationMs ? `${e.durationMs}ms` : ''); }
