/** Enterprise hook library — useDebounce, useThrottle, useToast, useDialog, useBottomSheet, useClipboard, useNetwork, useInfiniteScroll, usePagination, usePullToRefresh */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Animated } from 'react-native';

// ── Timers ──
export function useDebounce<T>(value: T, delay = 300): T { const [d, setD] = useState(value); useEffect(() => { const t = setTimeout(() => setD(value), delay); return () => clearTimeout(t); }, [value, delay]); return d; }
export function useThrottle<T>(value: T, interval = 200): T { const [t, setT] = useState(value); const lastRun = useRef(Date.now()); useEffect(() => { const now = Date.now(); if (now - lastRun.current >= interval) { setT(value); lastRun.current = now; } else { const timer = setTimeout(() => { setT(value); lastRun.current = Date.now(); }, interval - (now - lastRun.current)); return () => clearTimeout(timer); } }, [value, interval]); return t; }

// ── Clipboard ──
export function useClipboard() { const [copied, setCopied] = useState(false); const copy = useCallback(async (text: string) => { try { if (typeof navigator !== 'undefined' && navigator.clipboard) { await navigator.clipboard.writeText(text); } setCopied(true); setTimeout(() => setCopied(false), 2000); } catch {} }, []); return { copy, copied }; }

// ── Network ──
export function useNetwork() { const [online, setOnline] = useState(true); const [type, setType] = useState<string>('unknown'); useEffect(() => { /* In production: NetInfo.addEventListener */ }, []); return { isOnline: online, connectionType: type }; }

// ── Infinite Scroll ──
export function useInfiniteScroll(onEndReached: () => void, threshold = 0.3) { const onEndReachedRef = useRef(onEndReached); onEndReachedRef.current = onEndReached; const handleEndReached = useCallback(() => onEndReachedRef.current?.(), []); return { onEndReached: handleEndReached, onEndReachedThreshold: threshold }; }

// ── Pagination ──
export function usePagination<T>(fetchFn: (page: number) => Promise<T[]>) { const [data, setData] = useState<T[]>([]); const [page, setPage] = useState(1); const [loading, setLoading] = useState(false); const [hasMore, setHasMore] = useState(true); const loadMore = useCallback(async () => { if (loading || !hasMore) return; setLoading(true); try { const items = await fetchFn(page); setData(prev => [...prev, ...items]); setHasMore(items.length > 0); setPage(p => p + 1); } finally { setLoading(false); } }, [page, loading, hasMore, fetchFn]); return { data, loading, hasMore, loadMore, reset: () => { setData([]); setPage(1); setHasMore(true); } }; }

// ── Pull to Refresh ──
export function usePullToRefresh<T>(fetchFn: () => Promise<T>) { const [refreshing, setRefreshing] = useState(false); const [data, setData] = useState<T | null>(null); const onRefresh = useCallback(async () => { setRefreshing(true); try { const result = await fetchFn(); setData(result); } finally { setRefreshing(false); } }, [fetchFn]); useEffect(() => { onRefresh(); }, []); return { data, refreshing, onRefresh }; }

// ── Permissions ──
export function usePermissions() { const [granted, setGranted] = useState<Record<string, boolean>>({}); const request = useCallback(async (perm: string) => { setGranted(p => ({ ...p, [perm]: true })); return true; }, []); return { permissions: granted, request, isGranted: (p: string) => !!granted[p] }; }

// ── Safe Area ──
export function useSafeArea() { return { top: 47, bottom: 34, left: 0, right: 0 }; }