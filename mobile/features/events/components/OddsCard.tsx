/** OddsCard — betting odds display */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';

export function OddsCard({ odds, palette }: any) {
  if (!odds) return null;
  return (
    <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase' }]}>Odds ({odds.source})</Text>
      <View style={s.row}>
        <Text style={[typography.mono, { color: palette.text.primary }]}>{odds.fighterA}</Text>
        <Text style={[typography.mono, { color: palette.text.primary }]}>{odds.fighterB}</Text>
      </View>
    </View>
  );
}
const s = StyleSheet.create({
  card: { marginHorizontal: spacing.lg, padding: spacing.md, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
});
