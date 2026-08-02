/** Prediction card — odds and finish probability for a single fight */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';

export function FightPredictionCard({ prediction, palette }: any) {
  if (!prediction) return null;
  return (
    <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 8 }]}>Prediction</Text>
      <View style={s.row}><Text style={[typography.body, { color: palette.text.secondary }]}>Confidence</Text><Text style={[typography.body, { color: palette.primary[400], fontWeight: '700' }]}>{prediction.confidence?.score ?? '--'}/100</Text></View>
      <View style={s.row}><Text style={[typography.body, { color: palette.text.secondary }]}>Finish</Text><Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>
        {prediction.finish?.koTko > prediction.finish?.submission ? 'KO/TKO' : 'Submission'} • R{prediction.mostLikelyRound ?? '?'}
      </Text></View>
      {prediction.keyFactors?.slice(0, 2).map((kf: any, i: number) => (
        <View key={i} style={s.row}><Text style={[typography.bodySmall, { color: palette.text.secondary }]}>{kf.factor}</Text><Text style={[typography.bodySmall, { color: kf.impact > 0 ? '#10B981' : '#EF4444' }]}>{kf.impact > 0 ? '+' : ''}{kf.impact}</Text></View>
      ))}
    </View>
  );
}
const s = StyleSheet.create({
  card: { marginHorizontal: spacing.lg, padding: spacing.md, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
});
