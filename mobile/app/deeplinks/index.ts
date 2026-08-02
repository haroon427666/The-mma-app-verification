/** Deep Links — README + index */
/* 
## Deep Linking Platform

### Supported URL schemes
```
mma://event/:id          → EventDetail
mma://fighter/:id        → FighterProfile
mma://fight/:id          → FightDetail
mma://prediction/:id     → Prediction
mma://rankings           → Rankings
mma://watchlist          → Watchlist
mma://recommendations    → Recommendations
mma://profile            → Profile
https://mma-app.com/*    → Universal Link
```

### Hooks
- `useDeepLinks()` → parse, navigate, parseAndNavigate, buildLink
- `useShareLinks()` → share entities with generated URLs
- `useUniversalLinks()` → handle universal link URIs
*/

export { DeepLinkProvider, DeepLinkParser, linkParser, DeepLinkBuilder, linkBuilder, NavigationDispatcher, navigationDispatcher, RouteRegistry, routeRegistry, UniversalLinks, universalLinks, ShareLinks, shareLinks, QRLinks, qrLinks, LinkAnalytics, linkAnalytics, useLinkStore } from './DeeplinkManager';
export { useDeepLinks, useShareLinks, useUniversalLinks } from './DeeplinkHooks';
export { linkConfig, DEEPLINK_CONSTANTS, LinkLogger, linkLogger, linkUtils } from './DeeplinkTypes';
export type { LinkSource, RouteName, DeepLink, LinkConfig, ShareLink } from './DeeplinkTypes';
export { DeepLinkError, RouteError, ParsingError, ValidationError } from './DeeplinkTypes';
