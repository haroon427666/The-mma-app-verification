/** Rankings theme, charts, images, accessibility, errors, utils */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';

// ── Theme ──
export const rankingColors = {
  gold: '#F59E0B', silver: '#9CA3AF', bronze: '#CD7F32',
  movement: { up: '#10B981', down: '#EF4444', steady: '#6B7280', new: '#3B82F6' },
  streak: { win: '#10B981', loss: '#EF4444' },
  prospect: { rising: '#10B981', peak: '#3B82F6', declining: '#F97316' },
} as const;

export const WEIGHT_CLASSES = ['Heavyweight','Light Heavyweight','Middleweight','Welterweight','Lightweight','Featherweight','Bantamweight','Flyweight',"Women's Bantamweight","Women's Flyweight","Women's Strawweight"];

// ── Accessibility ──
export const rankingLabels = {
  card: (rank: number, name: string) => `Rank ${rank}: ${name}`,
  division: (name: string) => `${name} division rankings`,
  champion: (name: string) => `Champion: ${name}`,
  movement: (name: string, from: number, to: number) => `${name} moved from ${from} to ${to}`,
};

// ── Errors ──
export function RankingNotFound() {
  return <View style={er.center}><Text style={{ fontSize: 40 }}>🔍</Text><Text style={{ color: '#9CA3AF', marginTop: 8 }}>Ranking data not available</Text></View>;
}

// ── Utils ──
export function formatMovement(from: number | null, to: number): string {
  if (!from) return 'New entry';
  const diff = from - to;
  return diff > 0 ? `▲${diff}` : diff < 0 ? `▼${Math.abs(diff)}` : '—';
}

export function getTrajectoryColor(t: string): string {
  return rankingColors.prospect[t as keyof typeof rankingColors.prospect] || '#6B7280';
}

export function sortByRank<T extends { rank: number }>(items: T[]): T[] {
  return [...items].sort((a, b) => a.rank - b.rank);
}

export function sortByELO<T extends { fighter: { eloRating?: number | null } }>(items: T[]): T[] {
  return [...items].sort((a, b) => (b.fighter?.eloRating ?? 0) - (a.fighter?.eloRating ?? 0));
}

// ── Charts ──
export function RankProgressionChart({ data }: { data: Array<{ date: string; rank: number | null }> }) {
  return (
    <View style={er.chartWrap}>
      <Text style={[typography.subtitle, { color: '#FFF', marginBottom: spacing.md }]}>Rank Progression</Text>
      <View style={[er.chartPlaceholder, { backgroundColor: '#1A1A2E' }]}>
        <Text style={{ color: '#6B7280' }}>Chart (Victory/Reanimated)</Text>
      </View>
    </View>
  );
}

export function MovementTimelineChart({ data }: { data: any[] }) {
  return (
    <View style={er.chartWrap}>
      <View style={[er.chartPlaceholder, { backgroundColor: '#1A1A2E', height: 160 }]}>
        <Text style={{ color: '#6B7280' }}>Movement Timeline</Text>
      </View>
    </View>
  );
}

// ── Offline ──
export { useRankingsOffline } from '../stores';

const er = StyleSheet.create({
  center: { alignItems: 'center', paddingVertical: 60 },
  chartWrap: { marginBottom: spacing.xl },
  chartPlaceholder: { height: 200, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center' },
});
