/** FightRow — single fight row with names, ranks, result, prediction */
import React, { memo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';

export const FightRow = memo(({ fight, prediction, palette, onPress }: any) => (
  <TouchableOpacity onPress={onPress} style={[s.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} accessibilityRole="button">
    <View style={s.meta}>
      <Text style={[typography.caption, { color: palette.text.tertiary }]}>{fight.weightClass} • {fight.rounds}R</Text>
      {fight.isTitleFight && <Text style={s.champ}>🏆</Text>}
      {prediction && <Text style={[typography.caption, { color: palette.primary[400], fontWeight: '700' }]}>{Math.round(Math.max(prediction.probA ?? 0, prediction.probB ?? 0) * 100)}%</Text>}
    </View>
    <FName name={fight.fighterA?.fullName || fight.fighterAName} rank={fight.fighterA?.rank ?? fight.fighterARank} won={fight.result?.winnerId === fight.fighterA?.id} palette={palette} />
    <Text style={[typography.caption, { color: palette.text.tertiary, marginVertical: 3, marginLeft: 20 }]}>VS</Text>
    <FName name={fight.fighterB?.fullName || fight.fighterBName} rank={fight.fighterB?.rank ?? fight.fighterBRank} won={fight.result?.winnerId === fight.fighterB?.id} palette={palette} />
  </TouchableOpacity>
));

function FName({ name, rank, won, palette }: any) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', marginLeft: 8 }}>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: won ? '700' : '400' }]}>{name || 'TBD'}</Text>
      {rank && <Text style={[typography.caption, { color: '#F59E0B', marginLeft: 6 }]}>#{rank}</Text>}
      {won === true && <Text style={{ color: '#10B981', marginLeft: 6, fontWeight: '700' }}>W</Text>}
    </View>
  );
}
const s = StyleSheet.create({
  row: { padding: spacing.sm, marginHorizontal: spacing.lg, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 4 },
  meta: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  champ: { fontSize: 12, marginRight: 4 },
});
