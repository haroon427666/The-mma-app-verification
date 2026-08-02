/** Backoff Strategy + Cancellation Handler */
export class BackoffStrategy {
  static exponential(attempt: number, baseMs = 1000): number { return baseMs * Math.pow(2, attempt - 1) + Math.random() * baseMs; }
  static linear(attempt: number, baseMs = 1000): number { return baseMs * attempt; }
  static fixed(ms: number): number { return ms; }
}

export class CancellationHandler {
  private controllers = new Map<string, AbortController>();
  create(id: string): { signal: AbortSignal; cancel: () => void } {
    const ctrl = new AbortController(); this.controllers.set(id, ctrl); return { signal: ctrl.signal, cancel: () => { ctrl.abort(); this.controllers.delete(id); } };
  }
  cancelAll(): void { this.controllers.forEach((c) => c.abort()); this.controllers.clear(); }
  cancel(id: string): void { this.controllers.get(id)?.abort(); this.controllers.delete(id); }
}
export const cancellationHandler = new CancellationHandler();
