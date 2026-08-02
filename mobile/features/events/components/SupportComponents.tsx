/** Remaining components — Venue, Broadcast, Promotion, Results, Status, Sections, Loading, Error, Empty */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { typography, spacing, radius } from '@/theme';

// ── VenueCard ──
export function VenueCard({ venue, city, country, palette }: { venue: string; city: string; country: string; palette: any }) {
  return (
    <View style={[ss.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} accessibilityLabel={`Venue: ${venue}, ${city}, ${country}`}>
      <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase' }]}>📍 Venue</Text>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{venue}</Text>
      <Text style={[typography.caption, { color: palette.text.secondary }]}>{[city, country].filter(Boolean).join(', ')}</Text>
    </View>
  );
}

// ── BroadcastCard ──
export function BroadcastCard({ broadcasters, timezone, palette }: { broadcasters: string[]; timezone?: string; palette: any }) {
  return (
    <View style={[ss.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase' }]}>📺 Broadcast</Text>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{broadcasters?.length ? broadcasters.join(' / ') : 'TBA'}</Text>
      {timezone && <Text style={[typography.caption, { color: palette.text.secondary }]}>{timezone}</Text>}
    </View>
  );
}

// ── PromotionBadge ──
export function PromotionBadge({ promotion, palette }: { promotion: string; palette: any }) {
  return (
    <View style={[ss.badge, { backgroundColor: palette.primary[500] }]}>
      <Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{promotion}</Text>
    </View>
  );
}

// ── FightResult ──
export function FightResult({ winner, loser, method, round, time, palette }: any) {
  return (
    <View style={[ss.result, { borderColor: '#10B98133', backgroundColor: '#10B9810A' }]}>
      <Text style={[typography.bodySmall, { color: '#10B981', fontWeight: '700', textAlign: 'center' }]}>🏆 RESULT</Text>
      <Text style={[typography.body, { color: palette.text.primary, textAlign: 'center' }]}>{winner} def. {loser}</Text>
      <Text style={[typography.caption, { color: palette.text.secondary, textAlign: 'center' }]}>{method} • R{round} {time}</Text>
    </View>
  );
}

// ── FightStatus ──
export function FightStatus({ status, palette }: { status: string; palette: any }) {
  const map: Record<string, { label: string; color: string }> = {
    IN_PROGRESS: { label: 'LIVE', color: '#EF4444' },
    FINISHED: { label: 'Finished', color: '#10B981' },
    SCHEDULED: { label: 'Upcoming', color: palette.text.tertiary },
    CANCELLED: { label: 'Cancelled', color: '#EF4444' },
  };
  const config = map[status] ?? { label: status, color: palette.text.tertiary };
  return <Text style={[typography.caption, { color: config.color, fontWeight: '700' }]}>{config.label}</Text>;
}

// ── SectionHeader ──
export function SectionHeader({ title, count, palette }: { title: string; count?: number; palette: any }) {
  return (
    <View style={ss.sectionHead}>
      <Text style={[typography.title, { color: palette.text.primary, fontWeight: '700' }]}>{title}</Text>
      {count !== undefined && <Text style={[typography.bodySmall, { color: palette.text.tertiary }]}>{count}</Text>}
    </View>
  );
}

// ── LoadingCard ──
export function LoadingCard() {
  return (
    <View style={[ss.loadingWrap, { backgroundColor: '#1A1A2E', borderRadius: radius.md }]}>
      <ActivityIndicator color="#3B82F6" />
    </View>
  );
}

// ── ErrorCard ──
export function ErrorCard({ message, onRetry }: { message?: string; onRetry: () => void }) {
  return (
    <View style={ss.center}>
      <Text style={{ fontSize: 40 }}>⚠️</Text>
      <Text style={[typography.body, { color: '#9CA3AF', marginTop: 8 }]}>{message || 'Something went wrong'}</Text>
      <TouchableOpacity onPress={onRetry} style={ss.retry}><Text style={{ color: '#FFF', fontWeight: '600' }}>Retry</Text></TouchableOpacity>
    </View>
  );
}

// ── EmptyState ──
export function EmptyState({ message, palette }: { message: string; palette: any }) {
  return (
    <View style={[ss.center, { paddingVertical: 60 }]}>
      <Text style={[typography.body, { color: palette.text.secondary }]}>{message}</Text>
    </View>
  );
}

const ss = StyleSheet.create({
  card: { marginHorizontal: spacing.lg, padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 8 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, alignSelf: 'flex-start' },
  result: { padding: spacing.md, borderRadius: radius.md, borderWidth: 1, margin: spacing.lg },
  sectionHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.lg, marginBottom: spacing.sm },
  loadingWrap: { height: 80, marginHorizontal: spacing.lg, marginBottom: 12, alignItems: 'center', justifyContent: 'center' },
  center: { alignItems: 'center', paddingVertical: 40 },
  retry: { marginTop: 16, paddingVertical: 12, paddingHorizontal: 24, backgroundColor: '#3B82F6', borderRadius: 8 },
});
