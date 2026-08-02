/** Deep Links Hooks — useDeepLinks, useShareLinks, useUniversalLinks */
import { useState, useCallback } from 'react';
import { linkParser, linkBuilder, navigationDispatcher, universalLinks, shareLinks, qrLinks, useLinkStore } from './DeeplinkManager';
import type { DeepLink, LinkSource } from './DeeplinkTypes';

export function useDeepLinks() {
  const { lastLink, pendingLink } = useLinkStore();
  const parseAndNavigate = useCallback(async (url: string, source: LinkSource = 'deeplink') => {
    const link = linkParser.parse(url, source);
    await navigationDispatcher.dispatch(link);
    return link;
  }, []);
  return { lastLink, pendingLink, parse: linkParser.parse.bind(linkParser), navigate: navigationDispatcher.dispatch.bind(navigationDispatcher), parseAndNavigate, buildLink: linkBuilder.build.bind(linkBuilder) };
}

export function useShareLinks() {
  const [loading, setLoading] = useState(false);
  const share = useCallback(async (entityType: string, entityId: string, title: string, message?: string) => {
    setLoading(true); try { const link = shareLinks.generate(entityType, entityId, title); /* React Native Share */ return link; } finally { setLoading(false); }
  }, []);
  return { share, loading };
}

export function useUniversalLinks() {
  const [pending, setPending] = useState<DeepLink | null>(null);
  const handle = useCallback(async (url: string) => { const link = universalLinks.parse(url); setPending(link); await universalLinks.handle(url); setPending(null); return link; }, []);
  return { pending, handle };
}
