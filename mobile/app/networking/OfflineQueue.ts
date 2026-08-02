/** Offline Queue — queue mutations when offline, replay when online */
import { NetworkError, isRetryableError, isRetryableStatus } from './NetworkUtils';

interface QueuedRequest { id: string; execute: () => Promise<any>; resolve: (v: any) => void; reject: (e: any) => void; retries: number; maxRetries: number; timestamp: number; }

export class OfflineQueue {
  private queue: QueuedRequest[] = [];
  private processing = false;

  enqueue<T>(id: string, executor: () => Promise<T>, maxRetries = 3): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ id, execute: executor, resolve, reject, retries: 0, maxRetries, timestamp: Date.now() });
      this.processQueue();
    });
  }

  async processQueue(): Promise<void> {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;
    const item = this.queue[0];
    try {
      const result = await item.execute();
      item.resolve(result);
      this.queue.shift();
    } catch (error) {
      if (item.retries < item.maxRetries && (isRetryableError(error as Error) || (error as any)?.response?.status)) {
        item.retries++;
        await new Promise((r) => setTimeout(r, 1000 * item.retries));
      } else {
        item.reject(error);
        this.queue.shift();
      }
    }
    this.processing = false;
    this.processQueue();
  }

  get length(): number { return this.queue.length; }
  clear(): void { this.queue = []; }
}
export const offlineQueue = new OfflineQueue();
