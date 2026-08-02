/** Auth — README + Architecture + AuthenticationFlow + TokenLifecycle + Biometrics + Authorization + Testing + Migration */

/*
## Authentication Platform — Architecture

### Flow
```
AppBootstrap (Stage 5: auth)
  → AuthManager.restoreSession()
  → TokenStorage.getTokens()
  → TokenValidator.validate()
  → AuthStore.setAuthenticated()
```

### Token Lifecycle
```
Login → AccessToken(1h) + RefreshToken(30d)
  → 55min: RefreshManager.refresh()
  → Expired: AuthStore.setUnauthenticated()
  → Logout: TokenStorage.clearTokens()
```

### Biometric Authentication
```
biometricManager.isAvailable() → { available: true, type: 'face_id' }
biometricManager.authenticate('Sign in') → boolean
biometricManager.enroll() → boolean
```

### Authorization
```
Authorization.check(user.role, ['admin', 'moderator'])
Authorization.checkPermission(user.role, 'MANAGE_EVENTS')
withAuth(ProtectedScreen, ['admin'])  // Route guard HOC
```

### Hooks
- `useAuth()` → full auth state + context
- `useLogin()` → login mutation with loading/error
- `useLogout()` → logout mutation
- `useBiometric()` → biometric auth + enroll
- `useAuthorization()` → role + permission checks
- `useSession()` → session validation
- `useCurrentUser()` → user identity
- `usePermissions()` → permission check helper

### Roles
| Role | Access |
|---|---|
| user | View rankings, predictions |
| premium | Export data, advanced predictions |
| analyst | View analytics, export data |
| moderator | Manage events |
| admin | Full access, user management |

### Testing
```ts
it('validates tokens', () => { expect(TokenValidator.validate('valid_token_12345')).toBe(true); });
it('checks authorization', () => { expect(Authorization.check('admin', ['admin'])).toBe(true); });
```
*/

export * from './AuthTypes';
export * from './AuthStore';
export * from './AuthManager';
export * from './Authorization';
export * from './AuthHooks';
export * from './AuthAnalytics';
