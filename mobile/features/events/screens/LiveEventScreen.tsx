/** LiveEventScreen — real-time live event view with websocket-driven updates */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';
import { useEvent } from '../hooks/useEvent';
import { FightRow } from '../components/FightRow';
import { sortFightCard } from '../utils/fightSorter';

export function LiveEventScreen({ route }: any) {
  const { eventId } = route.params;
  const { palette } = useTheme();
  const { data: event } = useEvent(eventId);

  if (!event) return <View style={[st.root, { backgroundColor: palette.surface.bg }]} />;

  const fights = sortFightCard(event.fights ?? []);
  const currentFight = fights.find((f) => f.status === 'IN_PROGRESS');

  return (
    <SafeAreaView style={[st.root, { backgroundColor: '#000000' }]}>
      <View style={[st.liveHeader, { backgroundColor: '#EF4444' }]}>
        <Text style={[typography.bodySmall, { color: '#FFF', fontWeight: '700', letterSpacing: 2 }]}>● LIVE</Text>
        <Text style={[typography.body, { color: '#FFF', fontWeight: '600', marginTop: 4 }]}>{event.name}</Text>
      </View>

      {currentFight && (
        <View style={st.currentFight}>
          <Text style={[typography.caption, { color: '#EF4444', textAlign: 'center' }]}>CURRENT FIGHT</Text>
          <Text style={[typography.headline, { color: '#FFF', textAlign: 'center', marginTop: 8 }]}>
            {currentFight.fighterA?.lastName} vs {currentFight.fighterB?.lastName}
          </Text>
        </View>
      )}

      <Text style={[typography.subtitle, { color: '#FFF', paddingHorizontal: spacing.lg, marginTop: spacing.xl, marginBottom: spacing.md }]}>Fight Card</Text>

      {fights.map((fight) => (
        <FightRow key={fight.id} fight={fight} palette={{ ...palette, surface: { ...palette.surface, card: '#111', bg: '#000' }, text: { ...palette.text, primary: '#FFF', secondary: '#999' } }} compact />
      ))}
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  liveHeader: { padding: spacing.lg, alignItems: 'center', paddingTop: spacing.xxxl },
  currentFight: { padding: spacing.lg, marginTop: spacing.md },
});
