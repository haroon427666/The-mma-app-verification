/** Release — Hooks + README + index */
import { useState, useCallback } from 'react';
import { versionManager, buildManager, envManager, featureFlags, otaManager, releaseConfig } from './ReleaseManager';
import { storeMetadata, releaseNotes, crashManager, monitoring } from './ReleaseStores';
import type { BuildType, FeatureFlag, OTAUpdate } from './ReleaseManager';

export function useVersion() {
  return { version: versionManager.getVersion(), buildNumber: versionManager.getBuildNumber(), full: versionManager.getFullVersion(), bump: versionManager.bump.bind(versionManager) };
}

export function useFeatureFlag(key: string) {
  const [enabled, setEnabled] = useState(() => featureFlags.isEnabled(key));
  const [variant, setVariant] = useState(() => featureFlags.getVariant(key));
  const refresh = useCallback(() => { setEnabled(featureFlags.isEnabled(key)); setVariant(featureFlags.getVariant(key)); }, [key]);
  return { enabled, variant, refresh };
}

export function useOTA() {
  const [update, setUpdate] = useState<OTAUpdate | null>(null);
  const check = useCallback(async () => { const u = await otaManager.checkForUpdate(); setUpdate(u); return u; }, []);
  return { update, check, apply: otaManager.apply.bind(otaManager) };
}

/*
## Release Engineering Platform

### Build Pipeline
```
BuildManager.build(type) → BuildInfo { version, buildNumber, commit, timestamp }
VersionManager.bump('patch') → 1.0.1 (2)
EnvironmentManager.getMode() → 'production'

Fastlane → google_play lane / ios lane
StoreMetadata → generatePrivacyLabels / generateDataSafety
ReleaseNotes → generate + format
```

### Feature Flags
```ts
featureFlags.register({ key: 'new_search', name: 'New Search', enabled: true, rollout: 0.5, variants: { control: 0.5, variant_a: 0.5 } });
const { enabled, variant } = useFeatureFlag('new_search');
```

### OTA Updates
```ts
const { update, check, apply } = useOTA();
const update = await check(); // OTAUpdate | null
if (update?.mandatory) await otaManager.apply(update);
```
*/

export { ReleaseConfig, releaseConfig, VersionManager, versionManager, BuildManager, buildManager, EnvironmentManager, envManager, FeatureFlagService, featureFlags, OTAManager, otaManager, parseSemVer, formatVersion, bumpVersion, ReleaseLogger, releaseLogger } from './ReleaseManager';
export { StoreMetadataManager, storeMetadata, ReleaseNotesGenerator, releaseNotes, CrashManager, crashManager, MonitoringService, monitoring, fastlaneConfig } from './ReleaseStores';
export type { BuildType, ReleaseChannel, DeploymentTarget, SemVer, BuildInfo, StoreListing, ReleaseNote, FeatureFlag, OTAUpdate } from './ReleaseManager';
