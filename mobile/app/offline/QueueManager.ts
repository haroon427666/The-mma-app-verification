/** Queue System — persistent mutation queue with serialize/deserialize */
import type { Mutation, QueueEntry } from './OfflineTypes';
import { offlineLogger, generateId, OFFLINE_CONSTANTS } from './OfflineConfig';

export class QueueManager {
  private queue: QueueEntry<Mutation>[] = [];
  private log = offlineLogger;
  private processing = false;

  get length(): number { return this.queue.length; }
  get pending(): QueueEntry<Mutation>[] { return this.queue.filter((q) => q.status === 'pending'); }
  get failed(): QueueEntry<Mutation>[] { return this.queue.filter((q) => q.status === 'failed'); }

  enqueue(mutation: Mutation): void {
    if (this.queue.length >= OFFLINE_CONSTANTS.MAX_QUEUE_SIZE) { this.queue.shift(); }
    this.queue.push({ id: generateId(), entry: mutation, status: 'pending', addedAt: Date.now(), retries: 0 });
    this.log.info(`Queued mutation: ${mutation.type} ${mutation.endpoint}`);
  }

  dequeue(): QueueEntry<Mutation> | undefined {
    const item = this.queue.find((q) => q.status === 'pending');
    if (!item) return undefined;
    item.status = 'processing';
    return item;
  }

  complete(id: string): void {
    const item = this.queue.find((q) => q.id === id);
    if (item) item.status = 'completed';
  }

  fail(id: string): void {
    const item = this.queue.find((q) => q.id === id);
    if (item) { item.status = item.retries < OFFLINE_CONSTANTS.MAX_RETRIES ? 'pending' : 'failed'; item.retries++; }
  }

  cancel(id: string): void { this.queue = this.queue.filter((q) => q.id !== id); }
  pause(): void { this.processing = false; }
  resume(): void { this.processing = true; this.processQueue(); }
  clear(): void { this.queue = []; }

  async processQueue(): Promise<void> {
    if (!this.processing || this.queue.length === 0) return;
    const item = this.dequeue();
    if (!item) return;
    try {
      // In production: replay mutation via API
      this.complete(item.id);
    } catch {
      this.fail(item.id);
    }
    this.processQueue();
  }

  persist(): string { return JSON.stringify(this.queue); }
  load(json: string): void { try { this.queue = JSON.parse(json); } catch {} }
}
export const queueManager = new QueueManager();
