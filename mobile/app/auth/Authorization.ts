/** Authorization — role-based access control + permission guards */
import type { UserRole } from './AuthTypes';
import { AUTH_CONSTANTS, authUtils, AuthorizationError } from './AuthTypes';

export class Authorization {
  static check(role: UserRole, required: UserRole[]): boolean { return authUtils.hasRole(role, required); }
  static checkPermission(role: UserRole, permission: string): boolean { return authUtils.hasPermission(role, permission); }
  static guardRoute(role: UserRole, allowedRoles: UserRole[]): boolean {
    const allowed = this.check(role, allowedRoles);
    if (!allowed) throw new AuthorizationError(`Access denied: requires ${allowedRoles.join(',')}`);
    return true;
  }
}

export const ROLES = AUTH_CONSTANTS.ROLES;
export const PERMISSIONS = AUTH_CONSTANTS.PERMISSIONS as Record<string, UserRole[]>;

import { useAuthStore } from './AuthStore';
export function withAuth<P>(Component: React.ComponentType<P>, requiredRoles?: UserRole[]) {
  return function ProtectedRoute(props: P) {
    const { user, status } = useAuthStore();
    if (status !== 'authenticated') return null; // Redirect to login
    if (requiredRoles && user && !Authorization.check(user.role, requiredRoles)) return null; // Redirect to unauthorized
    return React.createElement(Component, props);
  };
}
