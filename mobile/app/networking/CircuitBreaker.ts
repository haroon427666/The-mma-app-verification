/** Circuit Breaker — prevents cascading failures */
export class CircuitBreaker {
  private failures = 0;
  private state: 'closed' | 'open' | 'half_open' = 'closed';
  private openUntil = 0;
  private threshold: number;
  private resetMs: number;

  constructor(threshold = 5, resetMs = 30000) { this.threshold = threshold; this.resetMs = resetMs; }

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() > this.openUntil) { this.state = 'half_open'; } else { throw new Error('Circuit breaker is open'); }
    }
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      throw err;
    }
  }

  private onSuccess(): void { this.failures = 0; this.state = 'closed'; }
  private onFailure(): void { this.failures++; if (this.failures >= this.threshold) { this.state = 'open'; this.openUntil = Date.now() + this.resetMs; } }

  get isOpen(): boolean { return this.state === 'open'; }
  reset(): void { this.failures = 0; this.state = 'closed'; }
}
export const circuitBreaker = new CircuitBreaker();
