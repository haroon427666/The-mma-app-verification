/** Security Hooks — useSecurity, useBiometric, usePrivacy, useThreatLevel */
import { useState, useCallback } from 'react';
import { securityManager, securityConfig, tokenSecurity, biometricSecurity, certPinning, antiTamper, privacyManager, useSecurityStore } from './SecurityManager';
import type { SecurityLevel } from './SecurityManager';
export { SecurityManager, securityManager, SecurityConfig, securityConfig, TokenSecurity, tokenSecurity, BiometricSecurity, biometricSecurity, CertificatePinning, certPinning, AntiTamper, antiTamper, PrivacyManager, privacyManager, SecurityLogger, securityLogger, securityUtils, useSecurityStore } from './SecurityManager';

export function useSecurity() {
  const store = useSecurityStore();
  const runCheck = useCallback(async () => { await securityManager.initialize(); }, []);
  return { threatScore: store.threatScore, securityEvents: store.securityEvents, runCheck, assess: () => securityManager.assessThreat() };
}

export function useBiometric() {
  const [loading, setLoading] = useState(false);
  const auth = useCallback(async (reason?: string) => { setLoading(true); try { return await biometricSecurity.authenticate(reason); } finally { setLoading(false); } }, []);
  const enroll = useCallback(async () => biometricSecurity.enroll(), []);
  return { authenticate: auth, enroll, loading, isAvailable: biometricSecurity.isAvailable };
}

export function usePrivacy() {
  return { maskEmail: privacyManager.maskEmail.bind(privacyManager), maskPII: privacyManager.maskPII.bind(privacyManager), secureLog: privacyManager.secureLog.bind(privacyManager), enableScreenshotProtection: privacyManager.enableScreenshotProtection.bind(privacyManager), blurOnBackground: privacyManager.blurOnBackground.bind(privacyManager) };
}

export function useThreatLevel() {
  const { threatScore } = useSecurityStore();
  const assess = useCallback(() => securityManager.assessThreat(), []);
  return { threatScore, assess };
}
