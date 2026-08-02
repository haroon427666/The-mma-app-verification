/** Security Platform — README + index */

/*
## Security & Privacy Platform

### Architecture
```
SecurityManager.initialize()
  → verifyCertificates (SSL pinning)
  → checkRoot / checkJailbreak / checkEmulator
  → verifyIntegrity (anti-tamper)
  → PrivacyManager.enableScreenshotProtection

Threat Assessment
  login_failed × N → score +30
  root_detected → score +100 (critical)
  debugger_detected → score +50 (high)
  → ThreatScore { score, level, factors }
```

### Features
- **Auth Security**: JWT lifecycle, token rotation, session fingerprinting
- **Encryption**: AES-256-GCM, RSA-2048, SHA-256, HMAC-SHA256
- **Biometric**: Face ID, Touch ID, fingerprint, PIN fallback, app lock
- **Certificate Pinning**: SSL pinning with backup pins, rotation
- **Anti-Tamper**: Hook detection, debugger detection, integrity checks
- **Privacy**: Screenshot protection, clipboard security, PII masking
- **Audit**: Security event tracking, threat scoring

### Hooks
- `useSecurity()` → threat score, events, run startup checks
- `useBiometric()` → authenticate, enroll
- `usePrivacy()` → maskEmail, maskPII, secure log, screenshot protection
- `useThreatLevel()` → threat assessment

### PII Masking
```ts
securityUtils.maskEmail('user@example.com')  → 'u***@example.com'
securityUtils.maskToken('eyJhbGci...xyz')     → 'eyJhbGci...xyz'
securityUtils.maskPhone('+1234567890')        → '*******7890'
securityUtils.stripPII('Contact user@x.com')  → 'Contact [REDACTED]'
```
*/

export * from './SecurityManager';
export * from './SecurityHooks';
