/** Rate Limiter — global request rate limiting with burst support */
import { networkConfig } from './NetworkConfig';

export class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private maxTokens: number;
  private refillRate: number;
  private waitQueue: Array<{ resolve: () => void }> = [];

  constructor(rpm = 60, burst = 10) {
    this.maxTokens = burst; this.tokens = burst; this.lastRefill = Date.now(); this.refillRate = rpm / 60000;
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) { this.tokens--; return; }
    return new Promise((resolve) => { this.waitQueue.push({ resolve }); });
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
    while (this.tokens >= 1 && this.waitQueue.length > 0) { this.tokens--; this.waitQueue.shift()?.resolve(); }
  }
}
export const rateLimiter = new RateLimiter();
