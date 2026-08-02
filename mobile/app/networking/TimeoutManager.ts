/** Timeout Manager — per-request and global timeout handling */
import { networkConfig } from './NetworkConfig';

export class TimeoutManager {
  private controllers = new Map<string, AbortController>();

  create(id: string, timeoutMs?: number): { signal: AbortSignal; clear: () => void } {
    const controller = new AbortController();
    this.controllers.set(id, controller);
    const ms = timeoutMs ?? networkConfig.get().timeout;
    const timer = setTimeout(() => controller.abort(), ms);
    return { signal: controller.signal, clear: () => { clearTimeout(timer); this.controllers.delete(id); } };
  }

  cancel(id: string): void { this.controllers.get(id)?.abort(); this.controllers.delete(id); }
  cancelAll(): void { this.controllers.forEach((c) => c.abort()); this.controllers.clear(); }
}
export const timeoutManager = new TimeoutManager();
