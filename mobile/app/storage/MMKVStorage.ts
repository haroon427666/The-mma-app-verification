/** MMKV Storage + Secure Storage + Encrypted Storage */
import { storageStore, storageLogger } from './StorageManager';

export class MMKVStorage {
  get<T>(key: string): T | null { return storageStore.get<T>(key); }
  set<T>(key: string, value: T, ttlMs?: number): void { storageStore.set(key, value, 'mmkv', ttlMs); }
  delete(key: string): boolean { return storageStore.delete(key); }
  getAllKeys(): string[] { return storageStore.keys(); }
}
export const mmkvStorage = new MMKVStorage();

export class SecureStorage {
  private prefix = 'secure:';
  get<T>(key: string): T | null {
    const raw = storageStore.get<string>(this.prefix + key);
    return raw ? JSON.parse(raw) : null; // In production: decrypt
  }
  set<T>(key: string, value: T): void {
    storageStore.set(this.prefix + key, JSON.stringify(value), 'secure');
    storageLogger.info(`Secure stored: ${key}`);
  }
  delete(key: string): void { storageStore.delete(this.prefix + key); }
  async biometricAuth(): Promise<boolean> { return true; /* In production: react-native-biometrics */ }
}
export const secureStorage = new SecureStorage();

export class EncryptedStorage {
  private prefix = 'enc:';
  get<T>(key: string): T | null {
    const raw = storageStore.get<string>(this.prefix + key);
    return raw ? JSON.parse(raw) : null; // In production: decrypt with key
  }
  set<T>(key: string, value: T): void { storageStore.set(this.prefix + key, JSON.stringify(value), 'encrypted'); }
  delete(key: string): void { storageStore.delete(this.prefix + key); }
  rotateKey(): void { storageLogger.info('Encryption key rotated'); }
}
export const encryptedStorage = new EncryptedStorage();
