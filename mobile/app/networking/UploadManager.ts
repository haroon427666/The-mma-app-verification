/** Upload + Download Manager */
import type { UploadProgress, DownloadProgress } from './NetworkTypes';

type ProgressCb = (p: UploadProgress) => void;

export class UploadManager {
  private active = new Map<string, { cancel: () => void; progress: UploadProgress }>();

  track(id: string, cancelFn: () => void, initial: UploadProgress): void {
    this.active.set(id, { cancel: cancelFn, progress: initial });
  }

  updateProgress(id: string, loaded: number, total: number): void {
    const entry = this.active.get(id);
    if (entry) entry.progress = { loaded, total, percentage: total > 0 ? loaded / total : 0 };
  }

  cancel(id: string): void { this.active.get(id)?.cancel(); this.active.delete(id); }
  getProgress(id: string): UploadProgress | undefined { return this.active.get(id)?.progress; }
  clear(): void { this.active.clear(); }
}
export const uploadManager = new UploadManager();

export class DownloadManager {
  private active = new Map<string, { cancel: () => void; progress: DownloadProgress }>();

  track(id: string, cancelFn: () => void, initial: DownloadProgress): void {
    this.active.set(id, { cancel: cancelFn, progress: initial });
  }

  updateProgress(id: string, loaded: number, total: number): void {
    const entry = this.active.get(id);
    if (entry) { const percentage = total > 0 ? loaded / total : 0; const speed = 0; entry.progress = { loaded, total, percentage, speed }; }
  }

  cancel(id: string): void { this.active.get(id)?.cancel(); this.active.delete(id); }
  get(id: string) { return this.active.get(id)?.progress; }
}
export const downloadManager = new DownloadManager();
