/** Storage Types */
export type StorageType = 'mmkv' | 'secure' | 'encrypted' | 'cache' | 'session' | 'preferences' | 'temporary' | 'persistent';
export type CacheStrategy = 'lru' | 'ttl' | 'fifo';
export type MigrationAction = 'none' | 'migrate' | 'rollback' | 'validate';

export interface StorageConfig {
  defaultType: StorageType; maxCacheEntries: number; defaultTTLMs: number;
  enableEncryption: boolean; enableCompression: boolean; enableMigration: boolean;
  autoCleanup: boolean; cleanupIntervalMs: number;
}

export interface StorageEntry<T = any> { key: string; value: T; type: StorageType; createdAt: number; ttlMs: number | null; accessCount: number; lastAccessed: number; }
export interface CacheStats { entries: number; hits: number; misses: number; hitRate: number; sizeBytes: number; }
export interface MigrationStep { version: number; up: () => void; down: () => void; }
export interface BackupData { version: number; timestamp: number; entries: Record<string, any>; checksum: string; }

export class StorageError extends Error { constructor(m: string, public type?: StorageType) { super(m); this.name = 'StorageError'; } }
export class EncryptionError extends StorageError { constructor(m: string) { super(m); this.name = 'EncryptionError'; } }
export class MigrationError extends StorageError { constructor(m: string) { super(m); this.name = 'MigrationError'; } }
export class ValidationError extends StorageError { constructor(m: string) { super(m); this.name = 'ValidationError'; } }
export class BackupError extends StorageError { constructor(m: string) { super(m); this.name = 'BackupError'; } }
export class SerializationError extends StorageError { constructor(m: string) { super(m); this.name = 'SerializationError'; } }
