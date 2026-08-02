# Storage Platform — README + Architecture

## Architecture
```
Feature Module
  → useStorage<T>() / useCache<T>() / usePreferences<T>() (hooks)
  → StorageManager → StorageStore (in-memory Map)
  → MMKVStorage | SecureStorage | EncryptedStorage | CacheStorage
  → StorageMigration | StorageBackup | StorageCleanup
```

## Storage Types (8)
| Type | Use Case |
|---|---|
| `mmkv` | General key-value storage |
| `secure` | Tokens, sessions, biometric data |
| `encrypted` | Sensitive user data |
| `cache` | Temporary API responses (TTL-based) |
| `session` | In-memory, cleared on app close |
| `preferences` | Theme, language, settings |
| `temporary` | Short-lived data (60s TTL) |
| `persistent` | Long-lived application data |

## Key Management
Centralized `StorageKeys` constant — never hardcode storage keys.

```tsx
import { StorageKeys, secureStorage } from '@/app/storage';
secureStorage.set(StorageKeys.AUTH_TOKEN, token);
```

## Hooks
```tsx
const { value: theme, set: setTheme } = usePreferences('theme_mode', 'dark');
const { value: token } = useSecureStorage(StorageKeys.AUTH_TOKEN);
const { value: cached, set: updateCache } = useCache('events_list', 300000);
const { value: session, remove } = useSession('current_filters');
```

## Migration
```tsx
storageMigration.register({ version: 1, up: () => { /* schema change */ }, down: () => { /* rollback */ } });
await storageMigration.migrate(1);
```

## Backup / Restore
```tsx
const backup = await storageBackup.export();
await storageBackup.import(backup);
```
