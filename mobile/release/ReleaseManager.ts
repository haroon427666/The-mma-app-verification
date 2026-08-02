/** Release Engineering — types, config, build, versioning, environment, feature flags */
export type BuildType = 'development' | 'staging' | 'production' | 'nightly';
export type ReleaseChannel = 'alpha' | 'beta' | 'production';
export type DeploymentTarget = 'google_play' | 'app_store' | 'ota';
export type SemVer = { major: number; minor: number; patch: number; };

export interface ReleaseConfig {
  appName: string; bundleId: string; packageName: string;
  version: SemVer; buildNumber: number; minSdkVersion: number;
  targetSdkVersion: number; enableOTA: boolean; enableFeatureFlags: boolean;
  crashReportingEnabled: boolean; analyticsEnabled: boolean;
}

export interface BuildInfo { type: BuildType; version: string; buildNumber: number; commit: string; timestamp: number; environment: string; }
export interface StoreListing { title: string; shortDescription: string; fullDescription: string; keywords: string[]; category: string; contentRating: string; }
export interface ReleaseNote { version: string; date: string; changes: string[]; fixes: string[]; known: string[]; }
export interface FeatureFlag { key: string; name: string; enabled: boolean; rollout: number; variants: Record<string, number>; }
export interface OTAUpdate { version: string; mandatory: boolean; minAppVersion: string; url: string; checksum: string; releaseNotes: string; }

export const defaultReleaseConfig: ReleaseConfig = {
  appName: 'MMA Intelligence', bundleId: 'com.mma.app', packageName: 'com.mma.app',
  version: { major: 1, minor: 0, patch: 0 }, buildNumber: 1,
  minSdkVersion: 26, targetSdkVersion: 34,
  enableOTA: true, enableFeatureFlags: true,
  crashReportingEnabled: true, analyticsEnabled: true,
};
let _rc: Partial<ReleaseConfig> = {};
export const releaseConfig = { get: (): ReleaseConfig => ({ ...defaultReleaseConfig, ..._rc }), update: (p: Partial<ReleaseConfig>) => { Object.assign(_rc, p); } };

export class ReleaseLogger { private p = '[Release]'; info(m: string) { console.log(`${this.p} ${m}`); } warn(m: string) { console.warn(`${this.p} ${m}`); } error(m: string) { console.error(`${this.p} ${m}`); } }
export const releaseLogger = new ReleaseLogger();

/** Release Manager — Build, Versioning, Environment, Feature Flags */
export function parseSemVer(v: string): SemVer { const [major, minor, patch] = v.split('.').map(Number); return { major: major || 1, minor: minor || 0, patch: patch || 0 }; }
export function formatVersion(v: SemVer): string { return `${v.major}.${v.minor}.${v.patch}`; }
export function bumpVersion(v: SemVer, type: 'major' | 'minor' | 'patch'): SemVer {
  if (type === 'major') return { major: v.major + 1, minor: 0, patch: 0 };
  if (type === 'minor') return { ...v, minor: v.minor + 1, patch: 0 };
  return { ...v, patch: v.patch + 1 };
}

export class VersionManager {
  private version: SemVer;
  private buildNum: number;
  constructor(version: SemVer, buildNum: number) { this.version = version; this.buildNum = buildNum; }
  getVersion(): string { return formatVersion(this.version); }
  getBuildNumber(): number { return this.buildNum; }
  bump(type: 'major' | 'minor' | 'patch'): SemVer { this.version = bumpVersion(this.version, type); this.buildNum++; return this.version; }
  getFullVersion(): string { return `${formatVersion(this.version)} (${this.buildNum})`; }
}
export const versionManager = new VersionManager(defaultReleaseConfig.version, defaultReleaseConfig.buildNumber);

export class BuildManager {
  private buildInfo: BuildInfo | null = null;
  getInfo(): BuildInfo | null { return this.buildInfo; }
  async build(type: BuildType): Promise<BuildInfo> {
    this.buildInfo = { type, version: versionManager.getVersion(), buildNumber: versionManager.getBuildNumber(), commit: 'HEAD', timestamp: Date.now(), environment: type === 'production' ? 'prod' : type };
    releaseLogger.info(`Build ${this.buildInfo.version} #${this.buildInfo.buildNumber} (${type})`);
    return this.buildInfo;
  }
}
export const buildManager = new BuildManager();

export class EnvironmentManager {
  private env: Record<string, string> = {};
  load(): Record<string, string> { return { ...this.env, ...process.env }; }
  get(key: string): string | undefined { return this.env[key]; }
  set(key: string, value: string): void { this.env[key] = value; }
  getMode(): BuildType { return (this.get('ENV') as BuildType) || 'development'; }
}
export const envManager = new EnvironmentManager();

export class FeatureFlagService {
  private flags = new Map<string, FeatureFlag>();
  register(flag: FeatureFlag): void { this.flags.set(flag.key, flag); }
  isEnabled(key: string): boolean { return this.flags.get(key)?.enabled ?? false; }
  getVariant(key: string): string { const f = this.flags.get(key); if (!f) return 'default'; const r = Math.random(); let cumulative = 0; for (const [name, pct] of Object.entries(f.variants)) { cumulative += pct; if (r < cumulative) return name; } return 'default'; }
  getAll(): FeatureFlag[] { return Array.from(this.flags.values()); }
  updateRollout(key: string, rollout: number): void { const f = this.flags.get(key); if (f) f.rollout = rollout; }
}
export const featureFlags = new FeatureFlagService();

export class OTAManager {
  private currentVersion: string = '';
  async checkForUpdate(): Promise<OTAUpdate | null> { return null; }
  async download(url: string): Promise<void> { /* Download update bundle */ }
  async apply(update: OTAUpdate): Promise<void> { /* Apply update + restart */ }
  async rollback(): Promise<void> { /* Rollback to previous bundle */ }
}
export const otaManager = new OTAManager();
