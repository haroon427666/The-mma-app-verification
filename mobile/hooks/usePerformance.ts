/** Production Performance — memoization, FlashList, bundle splitting, animation optimization.

  Import from '@hooks/usePerformance' or apply patterns directly.

  CRITICAL rules enforced:
  1. Every list item component MUST be React.memo'd
  2. Every callback passed to FlatList renderItem MUST be useCallback'd
  3. Zustand selectors MUST use shallow comparison or primitives
  4. Heavy computations MUST be in useMemo
  5. Image-heavy screens MUST use FlashList with estimatedItemSize
  6. Navigation transitions MUST use native driver
*/

import * as React from 'react';
import { useCallback, useMemo, useRef } from 'react';
import type { ReactElement } from 'react';

// ═══════════════════════════════════════════════════════════════════════════
// Zustand selector helpers — prevent unnecessary rerenders
// ═══════════════════════════════════════════════════════════════════════════

/** Extract a primitive from a Zustand store — zero allocations */
export function useStoreValue<T, K extends keyof T>(store: { getState: () => T }, key: K): T[K] {
  return store.getState()[key];
}

/** Compare two objects shallowly — for Zustand equalityFn */
export function shallow<T extends Record<string, unknown>>(a: T, b: T): boolean {
  if (a === b) return true;
  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) return false;
  return aKeys.every(k => a[k] === b[k]);
}

// ═══════════════════════════════════════════════════════════════════════════
// FlatList helpers — extract renderItem for React.memo
// ═══════════════════════════════════════════════════════════════════════════

/** Key extractor that handles objects with id field */
export const defaultKeyExtractor = (item: any, index: number) =>
  item?.id ?? `item-${index}`;

/** Estimated item size for FlashList virtualization */
export function estimatedItemSize(designTokenSize: number = 80): number {
  return designTokenSize;
}

/** getItemLayout for fixed-height lists — eliminates measurement */
export function fixedItemLayout(height: number) {
  return (_data: any, index: number) => ({
    length: height,
    offset: height * index,
    index,
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// Image optimization — CDN URL transforms
// ═══════════════════════════════════════════════════════════════════════════

/** Generate a thumbnail URL from a full-size image URL.
 *  ESPN CDN: append ?w=80&h=80
 *  Generic: return as-is
 */
export function thumbnailUrl(uri: string | null | undefined, size: number = 80): string | undefined {
  if (!uri) return undefined;
  if (uri.includes('espncdn.com')) return `${uri}?w=${size}&h=${size}`;
  if (uri.includes('cloudfront.net')) return `${uri}?width=${size}`;
  return uri;
}

/** Generate a medium URL for list cards */
export function mediumUrl(uri: string | null | undefined, width: number = 400): string | undefined {
  if (!uri) return undefined;
  if (uri.includes('espncdn.com')) return `${uri}?w=${width}`;
  return uri;
}

// ═══════════════════════════════════════════════════════════════════════════
// Render count tracker — dev-only, detects unnecessary rerenders
// ═══════════════════════════════════════════════════════════════════════════

export function useRenderCount(componentName: string, maxBeforeWarn: number = 10) {
  const count = useRef(0);
  count.current += 1;
  if (__DEV__ && count.current > maxBeforeWarn) {
    console.warn(`[PERF] ${componentName} rendered ${count.current} times — check memoization`);
  }
  return count.current;
}

// ═══════════════════════════════════════════════════════════════════════════
// Batch state updates — prevents cascading rerenders
// ═══════════════════════════════════════════════════════════════════════════

/** Batch multiple Zustand store updates into one render cycle.
 *  Usage: batchUpdates(() => { store1.setState(...); store2.setState(...); });
 */
export function batchUpdates(fn: () => void) {
  // React Native automatically batches in event handlers and lifecycle methods.
  // For async callbacks, wrap with unstable_batchedUpdates.
  if (typeof (global as any).nativeFabricUIManager !== 'undefined') {
    // Fabric — auto-batched
    fn();
  } else {
    // Paper — use React Native's batched updates
    const { unstable_batchedUpdates } = require('react-native');
    unstable_batchedUpdates(fn);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Memoized selector — compute derived data only when inputs change
// ═══════════════════════════════════════════════════════════════════════════

export function useMemoSelector<T, R>(
  store: { getState: () => T },
  selector: (state: T) => R,
  deps: unknown[] = [],
): R {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  return useMemo(() => selector(store.getState()), [store, ...deps]);
}

// ═══════════════════════════════════════════════════════════════════════════
// Navigation performance — freeze screens not in view
// ═══════════════════════════════════════════════════════════════════════════

/** Should this tab screen be kept alive when not focused? */
export const TAB_FREEZE_CONFIG: Record<string, boolean> = {
  home: false,          // Always keep alive (first tab)
  events: true,         // Freeze when not focused
  fighters: true,
  rankings: true,
  predictions: true,
  search: true,
  watchlist: true,
  notifications: false, // Keep alive for badge updates
  profile: false,      // Keep alive for session tracking
};

// ═══════════════════════════════════════════════════════════════════════════
// Bundle splitting — lazy imports for heavy screens
// ═══════════════════════════════════════════════════════════════════════════

/** Lazy-load a feature screen — splits it into its own bundle chunk.
 *  Usage: const FighterDetailScreen = lazyScreen(() => import('@/features/fighters/screens'));
 */
export function lazyScreen<T extends { default: React.ComponentType<any> }>(
  importFn: () => Promise<T>,
) {
  return React.lazy(importFn);
}

// Re-export React.memo, useMemo, useCallback for convenience
export { memo, useMemo, useCallback } from 'react';
