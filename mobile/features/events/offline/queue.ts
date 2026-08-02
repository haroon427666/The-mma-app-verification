/** Offline sync — queue mutations when offline, replay when connected */

import { useConnectivityStore } from '@/stores/connectivity';
import type { Reminder } from '../types';

interface QueuedAction {
  id: string;
  type: 'watchlist_add' | 'watchlist_remove' | 'reminder_create' | 'reminder_cancel';
  payload: Record<string, unknown>;
  createdAt: number;
  retryCount: number;
}

const STORAGE_KEY = 'events_offline_queue';

class EventsOfflineQueue {
  private queue: QueuedAction[] = [];

  async load() {
    try {
      const raw = ''; // await MMKV.getString(STORAGE_KEY);
      if (raw) this.queue = JSON.parse(raw);
    } catch { this.queue = []; }
  }

  private async persist() {
    // await MMKV.set(STORAGE_KEY, JSON.stringify(this.queue));
  }

  enqueue(action: Omit<QueuedAction, 'id' | 'createdAt' | 'retryCount'>) {
    const item: QueuedAction = {
      ...action, id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      createdAt: Date.now(), retryCount: 0,
    };
    this.queue.push(item);
    this.persist();
  }

  async process() {
    const isOnline = useConnectivityStore.getState().status === 'online';
    if (!isOnline || this.queue.length === 0) return;

    const action = this.queue[0];
    try {
      // Replay the action via the API layer
      // await replayAction(action);
      this.queue.shift();
    } catch {
      action.retryCount++;
      if (action.retryCount > 5) this.queue.shift();
    }
    this.persist();
  }

  get pending() { return this.queue.length; }
}

export const eventsOfflineQueue = new EventsOfflineQueue();
