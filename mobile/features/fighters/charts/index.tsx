/** Fighters Charts — Radar, Line, Bar, Pie, Momentum */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';

export function RadarChart({ stats, palette }: { stats: any; palette: any }) {
  if (!stats) return null;
  const dims = [
    { label: 'Striking', value: stats.sigStrikesLandedPerMin / 8 },
    { label: 'Accuracy', value: (stats.sigStrikesAccuracyPct ?? 50) / 100 },
    { label: 'Defense', value: (stats.sigStrikesDefensePct ?? 50) / 100 },
    { label: 'Grappling', value: stats.takedownAvgPer15 / 6 },
    { label: 'TD Def', value: (stats.takedownDefensePct ?? 50) / 100 },
    { label: 'Subs', value: stats.submissionAvgPer15 / 3 },
  ];
  return (
    <View style={ch.wrap}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.md }]}>Performance Radar</Text>
      {dims.map((d, i) => (
        <View key={i} style={ch.barWrap}>
          <Text style={[typography.caption, { color: palette.text.secondary, width: 70 }]}>{d.label}</Text>
          <View style={[ch.barBg, { backgroundColor: '#1E1E32' }]}>
            <View style={[ch.barFill, { width: `${Math.min((d.value ?? 0) * 100, 100)}%`, backgroundColor: palette.primary[400] }]} />
          </View>
        </View>
      ))}
    </View>
  );
}

export function LineChart({ data, palette }: { data: any; palette: any }) {
  return (
    <View style={ch.wrap}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.md }]}>Rank History</Text>
      <View style={[ch.chartPlaceholder, { backgroundColor: '#1A1A2E' }]}>
        <Text style={[typography.caption, { color: '#6B7280' }]}>Chart coming with Victory/Reanimated</Text>
      </View>
    </View>
  );
}

export function MomentumChart({ data, palette }: { data: any; palette: any }) {
  return (
    <View style={ch.wrap}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.md }]}>Momentum</Text>
      <View style={[ch.chartPlaceholder, { backgroundColor: '#1A1A2E' }]}>
        <Text style={[typography.caption, { color: '#6B7280' }]}>Chart coming with Victory/Reanimated</Text>
      </View>
    </View>
  );
}

const ch = StyleSheet.create({
  wrap: { marginBottom: spacing.xl },
  barWrap: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  barBg: { flex: 1, height: 12, borderRadius: 6, overflow: 'hidden', marginLeft: 8 },
  barFill: { height: 12, borderRadius: 6 },
  chartPlaceholder: { height: 200, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center' },
});
