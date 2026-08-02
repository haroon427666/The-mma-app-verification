/** FightCard — card segment header with fight rows */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import { FightRow } from './FightRow';
import type { FightCardEntry } from '../types';

export function FightCard({ segment, fights, predictions, palette, onFightPress }: {
  segment: string; fights: FightCardEntry[]; predictions?: Record<string, any>; palette: any; onFightPress?: (id: string) => void;
}) {
  return (
    <View style={s.section}>
      <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase', fontWeight: '700', marginLeft: spacing.lg, marginBottom: 6 }]}>{segment.replace(/([A-Z])/g, ' $1').trim()}</Text>
      {fights.map((f) => <FightRow key={f.id} fight={f} prediction={predictions?.[f.id]} palette={palette} onPress={() => onFightPress?.(f.id)} />)}
    </View>
  );
}
const s = StyleSheet.create({ section: { marginBottom: spacing.lg } });
