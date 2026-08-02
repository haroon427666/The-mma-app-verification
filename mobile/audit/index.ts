/** Audit — README + index */

/*
## Production Readiness Audit Platform

### Audit Categories (12)
| Category | Rules | Checks |
|---|---|---|
| architecture | 3 | Circular deps, folder consistency, dead code |
| performance | 3 | Startup time, bundle size, memory |
| security | 2 | No secrets, secure storage |
| accessibility | 2 | Labels, color contrast |
| design | 2 | Token compliance |
| offline | 1 | Queue functional |
| network | — | Response times, error rates |
| storage | — | Cache hit rate, migration |
| testing | — | Coverage, snapshots |
| errors | 2 | Boundaries, promises |
| documentation | 1 | README per module |
| dependencies | 2 | CVEs, unused packages |

### Usage
```ts
import { runFullAudit } from '@/audit';
const report = await runFullAudit();
// report = { overallScore: 95, readiness: 'ready', reports: [...], checklist: [...] }
```

### Report Output
```
Overall Score: 95% — READY
✓ No circular dependencies
✓ No hardcoded secrets
✓ Tokens in secure storage
✓ Labels present
⚠ Bundle size near limit
```

### Severity Levels
| Level | Action |
|---|---|
| critical | Launch blocker — must fix |
| high | Fix before submission |
| medium | Fix in next release |
| low | Nice-to-have |
| info | Advisory |
*/

export { AuditRunner, auditRunner, AuditReportGenerator, reportGenerator, runFullAudit, STANDARD_AUDIT_RULES, AuditLogger, auditLogger } from './AuditRunner';
export type { AuditSeverity, AuditCategory, AuditStatus, AuditRule, AuditResult, AuditReport, FinalAuditReport, ChecklistItem } from './AuditRunner';
