/** Retry Manager — exponential backoff for sync retries */
import { offlineConfig, offlineLogger } from './OfflineConfig';

export class RetryManager {
  private log = offlineLogger;

  async withRetry<T>(fn: () => Promise<T>, context: string): Promise<T> {
    let lastError: Error | undefined;
    const cfg = offlineConfig.get();

    for (let attempt = 0; attempt <= cfg.retryMaxAttempts; attempt++) {
      try {
        return await fn();
      } catch (err) {
        lastError = err as Error;
        if (attempt < cfg.retryMaxAttempts) {
          const delay = cfg.retryBackoffMs * Math.pow(2, attempt) + Math.random() * 500;
          this.log.warn(`Retry ${attempt + 1}/${cfg.retryMaxAttempts} for ${context} in ${Math.round(delay)}ms`);
          await new Promise((r) => setTimeout(r, delay));
        }
      }
    }
    throw lastError || new Error(`Failed after ${cfg.retryMaxAttempts} retries: ${context}`);
  }
}
export const retryManager = new RetryManager();
