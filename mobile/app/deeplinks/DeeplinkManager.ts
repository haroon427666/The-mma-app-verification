/** Deep Links — Parser, Builder, Router, Manager, Universal Links, Share Links, Analytics */
import { create } from 'zustand';
import React, { useEffect, useMemo } from 'react';
import type { DeepLink, LinkSource, RouteName, ShareLink, LinkConfig } from './DeeplinkTypes';
import { linkConfig, linkLogger, linkUtils, DEEPLINK_CONSTANTS, DeepLinkError, RouteError, ParsingError } from './DeeplinkTypes';

// ── Store ──
export const useLinkStore = create<{ lastLink: DeepLink | null; pendingLink: DeepLink | null; source: LinkSource | null }>(() => ({ lastLink: null, pendingLink: null, source: null }));

// ── Parser ──
export class DeepLinkParser {
  parse(url: string, source: LinkSource = 'deeplink'): DeepLink {
    try {
      let path: string; let scheme: string; let host: string;
      const cfg = linkConfig.get();
      if (url.startsWith('https://')) { const u = new URL(url); path = u.pathname.slice(1); scheme = 'https'; host = u.host; }
      else if (url.includes('://')) { const [s, rest] = url.split('://'); scheme = s; [host, path] = rest.includes('/') ? [rest.split('/')[0], rest.slice(rest.indexOf('/') + 1)] : [rest, '']; }
      else { path = url; scheme = cfg.scheme; host = cfg.host; }
      const routeKey = path.split('?')[0].split('/')[0];
      const route = (DEEPLINK_CONSTANTS.ROUTES as any)[routeKey] || 'Home';
      const params = linkUtils.parseParams(url.includes('?') ? url : `https://x?${path.split('?')[1] || ''}`);
      const mainPart = path.split('?')[0].split('/')[1];
      if (mainPart) params.id = mainPart;
      return { url, scheme, host, route, params, source, timestamp: Date.now() };
    } catch (e) { throw new ParsingError(url); }
  }
}
export const linkParser = new DeepLinkParser();

// ── Builder ──
export class DeepLinkBuilder {
  build(route: string, params?: Record<string, string>): string { return linkUtils.buildUrl(linkConfig.get(), route, params); }
  buildPredictionLink(predictionId: string): string { return this.build(`prediction/${predictionId}`); }
  buildFighterLink(fighterId: string): string { return this.build(`fighter/${fighterId}`); }
  buildEventLink(eventId: string): string { return this.build(`event/${eventId}`); }
  buildShareLink(title: string, description?: string): ShareLink { return { url: this.build('home'), title, description }; }
}
export const linkBuilder = new DeepLinkBuilder();

// ── Router ──
export class RouteRegistry {
  private routes = new Map<string, () => void>();
  register(name: string, handler: () => void): void { this.routes.set(name, handler); }
  navigate(link: DeepLink): void { const handler = this.routes.get(link.route); if (handler) { handler(); } else { throw new RouteError(link.route); } }
}
export const routeRegistry = new RouteRegistry();

export class NavigationDispatcher {
  async dispatch(link: DeepLink): Promise<void> {
    useLinkStore.setState({ lastLink: link, pendingLink: link, source: link.source });
    try { routeRegistry.navigate(link); linkLogger.info(`Navigated to ${link.route}`); }
    catch (e) { linkLogger.error('Navigation failed', e as Error); throw e; }
  }
}
export const navigationDispatcher = new NavigationDispatcher();

// ── Universal Links ──
export class UniversalLinks {
  parse(url: string): DeepLink { return linkParser.parse(url, 'universal'); }
  handle(url: string): Promise<void> { return navigationDispatcher.dispatch(this.parse(url)); }
}
export const universalLinks = new UniversalLinks();

// ── Share Links ──
export class ShareLinks {
  async share(link: DeepLink, title: string, message?: string): Promise<void> { /* React Native Share.share */ }
  generate(entityType: string, entityId: string, title: string): ShareLink { return { url: linkBuilder.build(`${entityType}/${entityId}`), title }; }
}
export const shareLinks = new ShareLinks();

// ── QR Links ──
export class QRLinks {
  generate(link: DeepLink): string { return link.url; }
  parse(data: string): DeepLink { return linkParser.parse(data, 'qr'); }
}
export const qrLinks = new QRLinks();

// ── Provider ──
export function DeepLinkProvider({ children, onLink }: { children: React.ReactNode; onLink?: (link: DeepLink) => void }) {
  useEffect(() => { if (onLink) { /* Subscribe to Linking.addEventListener */ } }, [onLink]);
  return React.createElement(React.Fragment, null, children);
}

// ── Analytics ──
export class LinkAnalytics { trackOpened(link: DeepLink): void {} trackShared(link: DeepLink): void {} trackQRScan(link: DeepLink): void {} trackFailure(url: string, error: Error): void {} }
export const linkAnalytics = new LinkAnalytics();
