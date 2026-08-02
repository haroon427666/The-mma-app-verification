/** ResultsScreen — post-event results with winners, methods, bonuses */

import React from 'react';
import { View, Text, ScrollView, FlatList, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';
import { useEvent } from '../hooks/useEvent';
import { sortFightCard } from '../utils/fightSorter';
import type { FightCardEntry } from '../types';

export function ResultsScreen({ route }: any) {
  const { eventId } = route.params;
  const { palette } = useTheme();
  const { data: event } = useEvent(eventId);

  if (!event) return <View style={[st.root, { backgroundColor: palette.surface.bg }]} />;

  const fights = sortFightCard(event.fights ?? []);
  const bonuses = event.results ? (event as any).bonuses : null;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary, marginBottom: 4 }]}>Results</Text>
        <Text style={[typography.bodySmall, { color: palette.text.secondary, marginBottom: spacing.xl }]}>{event.name}</Text>

        {fights.map((fight) => (
          <ResultRow key={fight.id} fight={fight} palette={palette} />
        ))}

        {bonuses && (
          <View style={[st.bonusCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: '#F59E0B', marginBottom: 12 }]}>Bonuses</Text>
            {bonuses.fightOfTheNight && (
              <Text style={[typography.body, { color: palette.text.primary }]}>🏆 FOTN: {bonuses.fightOfTheNight}</Text>
            )}
            {bonuses.performanceBonuses?.map((b: string, i: number) => (
              <Text key={i} style={[typography.bodySmall, { color: palette.text.secondary, marginTop: 4 }]}>💪 POTN: {b}</Text>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function ResultRow({ fight, palette }: { fight: FightCardEntry; palette: any }) {
  if (!fight.result) return null;
  const won = fight.result.winnerId === fight.fighterA?.id;

  return (
    <View style={[st.resultRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <Text style={[typography.body, { color: won ? palette.text.primary : palette.text.tertiary, fontWeight: won ? '700' : '400' }]}>
            {fight.fighterA?.fullName}
          </Text>
          <Text style={[typography.body, { color: !won ? palette.text.primary : palette.text.tertiary, fontWeight: !won ? '700' : '400' }]}>
            {fight.fighterB?.fullName}
          </Text>
        </View>
        <Text style={[typography.caption, { color: '#10B981', marginTop: 4 }]}>
          {fight.result.method} • R{fight.result.round} • {fight.result.time}
        </Text>
      </View>
    </View>
  );
}

function EventStatisticsScreen({ route }: any) {
  const { eventId } = route.params;
  const { palette } = useTheme();
  const { data: event } = useEvent(eventId);
  const stats = (event as any)?.statistics;

  if (!stats) return <View style={[st.root, { backgroundColor: palette.surface.bg }]} />;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary, marginBottom: spacing.xl }]}>Event Statistics</Text>
        {Object.entries(stats).filter(([, v]) => typeof v === 'number').map(([key, value]) => (
          <View key={key} style={st.statRow}>
            <Text style={[typography.body, { color: palette.text.secondary }]}>{key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase())}</Text>
            <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{value as number}</Text>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

export { EventStatisticsScreen };

const st = StyleSheet.create({
  root: { flex: 1 },
  resultRow: { padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 8 },
  bonusCard: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 1, marginTop: spacing.xl },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
});
