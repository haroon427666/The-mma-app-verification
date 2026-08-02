/** Retry Policy — exponential backoff with jitter */
import { isRetryableStatus, isRetryableError, buildRetryDelay } from './NetworkUtils';
import { networkConfig } from './NetworkConfig';

export function shouldRetry(attempt: number, error: any): boolean {
  if (attempt >= networkConfig.get().retryMaxAttempts) return false;
  if (error?.response) return isRetryableStatus(error.response.status);
  return isRetryableError(error);
}

export function getRetryDelay(attempt: number): number {
  return buildRetryDelay(attempt, 'exponential');
}

export async function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
