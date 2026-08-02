/** Release — Store listings, Fastlane config, store metadata, release notes */
import { releaseLogger } from './ReleaseManager';
import type { StoreListing, ReleaseNote } from './ReleaseManager';

export class StoreMetadataManager {
  private listings: Record<string, StoreListing> = {
    google_play: { title: 'MMA Intelligence', shortDescription: 'Complete MMA fight predictions, rankings, and recommendations.', fullDescription: 'MMA Intelligence delivers real-time fight predictions, comprehensive fighter rankings, personalized recommendations, and detailed fight analytics.', keywords: ['mma', 'ufc', 'fight', 'predictions', 'rankings', 'betting'], category: 'SPORTS', contentRating: 'Teen' },
    app_store: { title: 'MMA Intelligence', shortDescription: 'Fight predictions, rankings & MMA analytics.', fullDescription: 'MMA Intelligence delivers real-time fight predictions, comprehensive fighter rankings, personalized recommendations, and detailed fight analytics.', keywords: ['mma', 'ufc', 'fight', 'prediction', 'rankings'], category: 'Sports', contentRating: '12+' },
  };
  get(store: string): StoreListing | undefined { return this.listings[store]; }
  update(store: string, listing: Partial<StoreListing>): void { const existing = this.listings[store]; if (existing) Object.assign(existing, listing); }
  async generatePrivacyLabels(): Promise<Record<string, any>> { return { data_collected: { email: true, usage_data: true, crash_data: true }, data_not_collected: { financial_info: true, health_data: true, location: true } }; }
  async generateDataSafety(): Promise<Record<string, any>> { return { data_shared: false, data_collected: [{ type: 'Email', purpose: 'Account management' }, { type: 'App interactions', purpose: 'Analytics' }] }; }
}
export const storeMetadata = new StoreMetadataManager();

export class ReleaseNotesGenerator {
  private notes: ReleaseNote[] = [];
  generate(version: string, changes: string[], fixes: string[], known: string[] = []): ReleaseNote {
    const note: ReleaseNote = { version, date: new Date().toISOString().split('T')[0], changes, fixes, known };
    this.notes.unshift(note); return note;
  }
  getLatest(): ReleaseNote | undefined { return this.notes[0]; }
  getAll(): ReleaseNote[] { return this.notes; }
  format(notes: ReleaseNote): string {
    let out = `## v${notes.version} (${notes.date})\n\n`;
    if (notes.changes.length) { out += '### ✨ New\n' + notes.changes.map((c) => `- ${c}`).join('\n') + '\n\n'; }
    if (notes.fixes.length) { out += '### 🐛 Fixed\n' + notes.fixes.map((f) => `- ${f}`).join('\n') + '\n\n'; }
    if (notes.known.length) { out += '### ⚠ Known Issues\n' + notes.known.map((k) => `- ${k}`).join('\n') + '\n'; }
    return out;
  }
}
export const releaseNotes = new ReleaseNotesGenerator();

/** Fastlane helpers */
export const fastlaneConfig = {
  android: {
    lane: 'android beta', packageName: 'com.mma.app', jsonKeyFile: './fastlane/google-play-key.json',
    track: 'internal', releaseStatus: 'draft' as const,
    metadataPath: './fastlane/metadata/android',
    changelogsPath: './fastlane/metadata/android/changelogs',
  },
  ios: {
    lane: 'ios beta', bundleId: 'com.mma.app', appIdentifier: 'com.mma.app',
    teamId: '', itcTeamId: '',
    metadataPath: './fastlane/metadata/ios',
  },
};

export class CrashManager {
  private enabled = true;
  setEnabled(v: boolean): void { this.enabled = v; }
  recordError(error: Error, context?: string): void { if (this.enabled) releaseLogger.error(`Crash: ${error.message}`, error); }
  setUser(id: string, email?: string): void { /* Set user context */ }
  log(message: string): void { releaseLogger.info(`[Crash] ${message}`); }
}
export const crashManager = new CrashManager();

export class MonitoringService {
  trackRelease(version: string): void { releaseLogger.info(`Release ${version} deployed`); }
  trackAdoption(version: string, users: number): void { /* Track adoption rate */ }
  trackCrashRate(version: string, rate: number): void { /* Track crash-free rate */ }
  trackANR(count: number): void { /* Track ANR count */ }
  getHealth(): { status: string; uptime: number } { return { status: 'healthy', uptime: Date.now() }; }
}
export const monitoring = new MonitoringService();
