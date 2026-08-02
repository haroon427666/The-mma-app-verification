/** Auth Platform — barrel export */
export { useAuthStore, AuthContext, AuthProvider } from './AuthStore';
export { AuthService, authService, AuthManager, authManager, TokenStorage, TokenValidator, RefreshManager, refreshManager, BiometricManager, biometricManager } from './AuthManager';
export { Authorization, ROLES, PERMISSIONS, withAuth } from './Authorization';
export { useAuth, useLogin, useLogout, useCurrentUser, useBiometric, useAuthorization, useSession, usePermissions } from './AuthHooks';
export { AuthAnalytics, authAnalytics, AuthMetricsCollector, authMetrics } from './AuthAnalytics';
export { authConfig, AUTH_CONSTANTS, AuthLogger, authLogger, authUtils, authEvents } from './AuthTypes';
export type { AuthStatus, BiometricType, AuthMethod, AuthConfig, UserIdentity, UserRole, AuthTokens, LoginRequest, AuthEvent, AuthMetrics } from './AuthTypes';
export { AuthenticationError, AuthorizationError, TokenExpiredError, RefreshError, BiometricError, SessionError } from './AuthTypes';
