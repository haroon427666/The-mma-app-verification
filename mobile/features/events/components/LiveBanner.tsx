/** LiveBanner — featured live event banner */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import type { ExtendedEvent } from '../types';

export function LiveBanner({ event, palette, onPress }: { event: ExtendedEvent; palette: any; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={[s.banner, { backgroundColor: '#EF4444' }]} accessibilityRole="button" accessibilityLabel={`Live now: ${event.name}`}>
      <View style={s.pulse} />
      <Text style={[s.tag, { color: '#FFF' }]}>🔴 LIVE NOW</Text>
      <Text style={[typography.body, { color: '#FFF', fontWeight: '600', marginTop: 4 }]} numberOfLines={2}>{event.name}</Text>
      <Text style={[typography.caption, { color: '#FFFC', marginTop: 2 }]}>{event.fightCount} fights • {event.broadcasters?.[0]}</Text>
    </TouchableOpacity>
  );
}
const s = StyleSheet.create({
  banner: { margin: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, alignItems: 'center' },
  pulse: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#FFF', marginBottom: 8 },
  tag: { fontWeight: '700', letterSpacing: 1, fontSize: 12 },
});
