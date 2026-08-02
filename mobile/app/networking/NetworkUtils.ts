/** Network Utilities */
import { defaultNetworkConfig } from './NetworkConfig';

export function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function buildRetryDelay(attempt: number, strategy?: string): number {
  const cfg = defaultNetworkConfig;
  if (strategy === 'linear') return cfg.retryBackoffMs * attempt;
  // exponential with optional jitter
  const base = cfg.retryBackoffMs * Math.pow(2, attempt - 1);
  if (cfg.retryJitter) return base + Math.random() * base * 0.5;
  return base;
}

export function isRetryableStatus(status: number): boolean {
  return status === 0 || status === 408 || status === 429 || (status >= 500 && status <= 599);
}

export function isRetryableError(error: Error): boolean {
  return error.message?.includes('timeout') || error.message?.includes('network') || error.message?.includes('ECONNRESET') || false;
}

export function sanitizeUrl(url: string): string {
  return url.replace(/\/\//g, '/').replace(':/', '://');
}
