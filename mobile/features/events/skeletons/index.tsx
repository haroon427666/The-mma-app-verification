/** Skeletons — per-component skeleton loaders */
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { spacing, radius } from '@/theme';

const SS = { backgroundColor: '#1A1A2E', borderRadius: radius.sm };

export function EventCardSkeleton() {
  return <View style={s.row}><View style={[s.date, SS]} /><View style={{ flex: 1 }}><View style={[s.lineWide, SS]} /><View style={[s.line, SS]} /></View></View>;
}

export function FightCardSkeleton() {
  return <View style={s.card}><View style={[s.lineWide, SS]} /><View style={[s.line, SS]} /><View style={[s.lineSmall, SS]} /></View>;
}

export function DetailSkeleton() {
  return (
    <View style={s.detailWrap}>
      <View style={[s.banner, SS]} />
      {[1,2,3].map((i) => <View key={i} style={[s.block, SS]} />)}
    </View>
  );
}

export function PredictionSkeleton() {
  return (
    <View style={s.card}>
      <View style={[s.lineWide, SS]} />
      <View style={[s.line, SS]} />
      <View style={[s.line, SS]} />
      <View style={[s.lineSmall, SS]} />
    </View>
  );
}

export function ResultsSkeleton() {
  return <View style={s.detailWrap}>{[1,2,3,4,5].map((i) => <View key={i} style={[s.block, SS]} />)}</View>;
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', padding: spacing.md, marginHorizontal: spacing.lg, gap: 12, marginBottom: 8 },
  date: { width: 48, height: 48, borderRadius: 10 },
  lineWide: { height: 16, width: '80%', marginBottom: 6 },
  line: { height: 12, width: '60%', marginBottom: 4 },
  lineSmall: { height: 10, width: '40%' },
  card: { padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 8, borderRadius: radius.md },
  detailWrap: { padding: spacing.lg },
  banner: { height: 200, borderRadius: radius.lg, marginBottom: spacing.lg },
  block: { height: 80, borderRadius: radius.md, marginBottom: 12 },
});
