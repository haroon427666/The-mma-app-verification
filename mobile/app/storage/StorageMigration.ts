/** Storage Migration + Backup/Restore + Cleanup */
import { storageLogger, storageUtils } from './StorageConfig';
import { storageStore } from './StorageManager';
import type { MigrationStep, BackupData } from './StorageTypes';

export class StorageMigration {
  private currentVersion = 1;
  private migrations: MigrationStep[] = [];

  register(step: MigrationStep): void { this.migrations.push(step); }

  async migrate(targetVersion: number): Promise<void> {
    const current = storageStore.get<number>('__storage_version__') ?? 0;
    if (current >= targetVersion) return;
    storageLogger.info(`Migrating from v${current} to v${targetVersion}`);

    for (const step of this.migrations) {
      if (step.version > current && step.version <= targetVersion) {
        try { step.up(); storageLogger.info(`Migration v${step.version} complete`); }
        catch (err) { storageLogger.error(`Migration v${step.version} failed`, err as Error); step.down(); throw err; }
      }
    }
    storageStore.set('__storage_version__', targetVersion, 'persistent');
  }

  rollback(toVersion: number): void {
    const steps = this.migrations.filter((s) => s.version > toVersion).reverse();
    steps.forEach((s) => { try { s.down(); } catch {} });
  }
}
export const storageMigration = new StorageMigration();

export class StorageBackup {
  async export(): Promise<BackupData> {
    const entries = storageStore.getAll();
    return { version: 1, timestamp: Date.now(), entries, checksum: '' };
  }

  async import(data: BackupData): Promise<void> {
    Object.entries(data.entries).forEach(([k, v]) => storageStore.set(k, v));
    storageLogger.info(`Backup imported: ${Object.keys(data.entries).length} entries`);
  }

  async verify(data: BackupData): Promise<boolean> { return data.entries != null && data.version > 0; }
}
export const storageBackup = new StorageBackup();

export class StorageCleanup {
  cleanup(): void {
    storageStore.cleanup();
    storageLogger.info('Cleanup complete');
  }
  scheduleCleanup(intervalMs = 60 * 60_1000): void { setInterval(() => this.cleanup(), intervalMs); }
}
export const storageCleanup = new StorageCleanup();
