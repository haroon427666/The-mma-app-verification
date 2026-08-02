/** Storage Platform — barrel export */
export { StorageManager, storageManager, storageStore, useStorageState } from './StorageManager';
export { MMKVStorage, mmkvStorage } from './MMKVStorage';
export { SecureStorage, secureStorage, EncryptedStorage, encryptedStorage } from './MMKVStorage';
export { CacheStorage, cacheStorage, SessionStorage, sessionStorage, PreferencesStorage, preferencesStorage, TemporaryStorage, temporaryStorage, PersistentStorage, persistentStorage } from './CacheStorage';
export { StorageKeys, KeyManager, keyManager } from './KeyManager';
export { StorageEncryption, storageEncryption, StorageCompression, storageCompression, StorageSerializer, storageSerializer, StorageValidator, storageValidator } from './StorageEncryption';
export { StorageMigration, storageMigration, StorageBackup, storageBackup, StorageCleanup, storageCleanup } from './StorageMigration';
export { StorageMetrics, StorageAnalytics, storageAnalytics } from './StorageMetrics';
export { storageConfig, STORAGE_CONSTANTS, StorageLogger, storageLogger } from './StorageConfig';
export { useStorage, useCache, usePreferences, useSession, useSecureStorage, usePersistentStorage } from './StorageHooks';
export type { StorageType, CacheStrategy, MigrationAction, StorageConfig, StorageEntry, CacheStats, MigrationStep, BackupData } from './StorageTypes';
export { StorageError, EncryptionError, MigrationError, ValidationError, BackupError, SerializationError } from './StorageTypes';
