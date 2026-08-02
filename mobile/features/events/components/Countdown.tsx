/** Countdown — 4-box countdown timer */
import React, { memo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import type { CountdownState } from '../types';

export const Countdown = memo(({ state, palette }: { state: CountdownState; palette: any }) => {
  if (state.isPast) return <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', padding: spacing.lg }]}>Event has started</Text>;
  return (
    <View style={[s.wrap, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.caption, { color: state.isStartingSoon ? '#F59E0B' : palette.text.secondary, textAlign: 'center' }]}>
        {state.isStartingSoon ? '⚡ Starting soon' : 'Starts in'}
      </Text>
      <View style={s.row}>
        {[{ v: state.days, l: 'Days' }, { v: state.hours, l: 'Hrs' }, { v: state.minutes, l: 'Min' }, { v: state.seconds, l: 'Sec' }].map(({ v, l }) => (
          <View key={l} style={[s.box, { backgroundColor: palette.surface.elevated }]}>
            <Text style={[typography.title, { color: palette.text.primary, fontWeight: '700' }]}>{String(v).padStart(2, '0')}</Text>
            <Text style={[typography.caption, { color: palette.text.tertiary }]}>{l}</Text>
          </View>
        ))}
      </View>
    </View>
  );
});
const s = StyleSheet.create({
  wrap: { marginHorizontal: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  row: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginTop: 12 },
  box: { width: 56, height: 56, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
});
