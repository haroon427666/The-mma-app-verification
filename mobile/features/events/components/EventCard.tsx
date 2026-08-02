/** EventCard — date badge, venue, fight count, status indicator */
import React, { memo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import { isLive } from '../utils/eventStatus';
import type { ExtendedEvent } from '../types';

export const EventCard = memo(({ event, palette, onPress }: { event: ExtendedEvent; palette: any; onPress: () => void }) => {
  const live = isLive(event);
  const d = new Date(event.date || event.startTime);
  return (
    <TouchableOpacity onPress={onPress} style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} accessibilityRole="button" accessibilityLabel={`${event.name}, ${d.toLocaleDateString()}`}>
      <View style={[s.date, { backgroundColor: live ? '#EF4444' : palette.surface.elevated }]}>
        <Text style={[s.day, { color: live ? '#FFF' : palette.text.primary }]}>{d.getDate()}</Text>
        <Text style={[s.month, { color: live ? '#FFFC' : palette.text.secondary }]}>{d.toLocaleDateString('en-US', { month: 'short' })}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          {live && <View style={s.liveBadge}><Text style={s.liveText}>LIVE</Text></View>}
          <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600', flex: 1 }]} numberOfLines={1}>{event.name}</Text>
        </View>
        <Text style={[typography.caption, { color: palette.text.secondary }]}>{event.venue} • {event.city}</Text>
        <Text style={[typography.caption, { color: palette.text.tertiary }]}>{event.fightCount} fights</Text>
      </View>
    </TouchableOpacity>
  );
});
const s = StyleSheet.create({
  card: { flexDirection: 'row', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 8, borderRadius: radius.md, borderWidth: 0.5 },
  date: { width: 48, height: 48, borderRadius: 10, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  day: { fontSize: 20, fontWeight: '700' }, month: { fontSize: 11, fontWeight: '600', textTransform: 'uppercase' },
  liveBadge: { backgroundColor: '#EF4444', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginRight: 8 },
  liveText: { color: '#FFF', fontSize: 10, fontWeight: '700' },
});
