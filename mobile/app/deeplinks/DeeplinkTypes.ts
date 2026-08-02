/** Deep Links Platform — all types, config, constants, errors, logger, utils */
export type LinkSource = 'universal' | 'app_link' | 'deeplink' | 'push' | 'share' | 'qr' | 'external';
export type RouteName = 'EventDetail' | 'FighterProfile' | 'FightDetail' | 'Prediction' | 'Rankings' | 'Watchlist' | 'Recommendations' | 'Profile' | 'Settings' | 'Home';
export interface DeepLink { url: string; scheme: string; host: string; route: RouteName; params: Record<string, string>; source: LinkSource; timestamp: number; }
export interface LinkConfig { scheme: string; host: string; universalLinkHost: string; androidPackageName: string; iosBundleId: string; }
export interface ShareLink { url: string; title: string; description?: string; imageUrl?: string; }

export class DeepLinkError extends Error { constructor(m: string) { super(m); this.name = 'DeepLinkError'; } }
export class RouteError extends DeepLinkError { constructor(r: string) { super(`Unknown route: ${r}`); this.name = 'RouteError'; } }
export class ParsingError extends DeepLinkError { constructor(u: string) { super(`Cannot parse URL: ${u}`); this.name = 'ParsingError'; } }
export class ValidationError extends DeepLinkError { constructor(m: string) { super(m); this.name = 'ValidationError'; } }

export const defaultLinkConfig: LinkConfig = { scheme: 'mma', host: 'app', universalLinkHost: 'mma-app.com', androidPackageName: 'com.mma.app', iosBundleId: 'com.mma.app' };
const _lc: Partial<LinkConfig> = {};
export const linkConfig = { get: (): LinkConfig => ({ ...defaultLinkConfig, ..._lc }), update: (p: Partial<LinkConfig>) => { Object.assign(_lc, p); } };

export const DEEPLINK_CONSTANTS = {
  ROUTES: { 'event': 'EventDetail', 'fighter': 'FighterProfile', 'fight': 'FightDetail', 'prediction': 'Prediction', 'rankings': 'Rankings', 'watchlist': 'Watchlist', 'recommendations': 'Recommendations', 'profile': 'Profile', 'settings': 'Settings', 'home': 'Home' } as Record<string, RouteName>,
  PATTERNS: { event: /^event\/([a-zA-Z0-9-]+)$/, fighter: /^fighter\/([a-zA-Z0-9-]+)$/, fight: /^fight\/([a-zA-Z0-9-]+)$/, prediction: /^prediction\/([a-zA-Z0-9-]+)$/ },
} as const;
export class LinkLogger { private p = '[Deeplinks]'; info(m: string) { console.log(`${this.p} ${m}`); } error(m: string, e?: Error) { console.error(`${this.p} ${m}`, e?.message ?? ''); } }
export const linkLogger = new LinkLogger();
export const linkUtils = { buildUrl: (cfg: LinkConfig, route: string, params?: Record<string, string>): string => { const q = params ? '?' + new URLSearchParams(params).toString() : ''; return `${cfg.scheme}://${cfg.host}/${route}${q}`; }, parseParams: (url: string): Record<string, string> => { try { const u = new URL(url); const p: Record<string, string> = {}; u.searchParams.forEach((v, k) => { p[k] = v; }); return p; } catch { return {}; } } };