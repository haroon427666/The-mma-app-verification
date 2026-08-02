/** FightCardScreen — focused view of a single fight with predictions and fighter details */

import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';
import { useEvent } from '../hooks/useEvent';
import { useFightPrediction } from '../hooks/usePredictions';

export function FightCardScreen({ route, navigation }: any) {
  const { eventId, fightId } = route.params;
  const { palette } = useTheme();
  const { data: event } = useEvent(eventId);

  const fight = event?.fights?.find((f) => f.id === fightId);
  const { data: prediction } = useFightPrediction?.(fightId) ?? {};

  if (!fight) return <View style={[st.root, { backgroundColor: palette.surface.bg }]} />;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <View style={[st.header, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
          {fight.isTitleFight && <Text style={st.titleBadge}>🏆 TITLE FIGHT</Text>}
          <Text style={[typography.caption, { color: palette.text.tertiary }]}>{fight.weightClass} • {fight.rounds} rounds</Text>
        </View>

        <View style={st.fighters}>
          <TouchableOpacity style={[st.fighterCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} onPress={() => {/* navigate to fighter */}}>
            <View style={st.avatar}><Text style={{ fontSize: 28 }}>🥊</Text></View>
            <Text style={[typography.title, { color: palette.text.primary, textAlign: 'center', marginTop: 8 }]}>{fight.fighterA?.fullName ?? 'TBD'}</Text>
            <Text style={[typography.caption, { color: palette.text.secondary }]}>{fight.fighterA?.record}</Text>
            {fight.fighterA?.rank && <Text style={[typography.caption, { color: '#F59E0B' }]}>#{fight.fighterA.rank}</Text>}
            {prediction && (
              <View style={[st.predBadge, { backgroundColor: prediction.probA > 0.5 ? '#10B981' : palette.surface.elevated }]}>
                <Text style={[typography.bodySmall, { color: '#FFF', fontWeight: '700' }]}>{Math.round(prediction.probA * 100)}%</Text>
              </View>
            )}
          </TouchableOpacity>

          <Text style={[typography.headline, { color: palette.text.tertiary, marginTop: 30 }]}>VS</Text>

          <TouchableOpacity style={[st.fighterCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} onPress={() => {/* navigate to fighter */}}>
            <View style={st.avatar}><Text style={{ fontSize: 28 }}>🥊</Text></View>
            <Text style={[typography.title, { color: palette.text.primary, textAlign: 'center', marginTop: 8 }]}>{fight.fighterB?.fullName ?? 'TBD'}</Text>
            <Text style={[typography.caption, { color: palette.text.secondary }]}>{fight.fighterB?.record}</Text>
            {fight.fighterB?.rank && <Text style={[typography.caption, { color: '#F59E0B' }]}>#{fight.fighterB.rank}</Text>}
            {prediction && (
              <View style={[st.predBadge, { backgroundColor: prediction.probB > 0.5 ? '#10B981' : palette.surface.elevated }]}>
                <Text style={[typography.bodySmall, { color: '#FFF', fontWeight: '700' }]}>{Math.round(prediction.probB * 100)}%</Text>
              </View>
            )}
          </TouchableOpacity>
        </View>

        {prediction && (
          <View style={[st.predCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Prediction</Text>
            <View style={st.predRow}>
              <Text style={[typography.body, { color: palette.text.secondary }]}>Confidence</Text>
              <Text style={[typography.body, { color: palette.primary[400], fontWeight: '700' }]}>{prediction.confidence.score}/100</Text>
            </View>
            <View style={st.predRow}>
              <Text style={[typography.body, { color: palette.text.secondary }]}>Most Likely Finish</Text>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>
                {prediction.finish.koTko > prediction.finish.submission ? 'KO/TKO' : 'Submission'} R{prediction.mostLikelyRound}
              </Text>
            </View>
            {prediction.keyFactors?.slice(0, 3).map((kf, i) => (
              <View key={i} style={st.factor}>
                <Text style={[typography.bodySmall, { color: palette.text.primary }]}>{kf.factor}</Text>
                <Text style={[typography.bodySmall, { color: kf.impact > 0 ? '#10B981' : '#EF4444' }]}>{kf.impact > 0 ? '+' : ''}{kf.impact}</Text>
              </View>
            ))}
          </View>
        )}

        {fight.result && (
          <View style={[st.resultCard, { backgroundColor: '#10B98115', borderColor: '#10B98133' }]}>
            <Text style={[typography.subtitle, { color: '#10B981', textAlign: 'center' }]}>Result</Text>
            <Text style={[typography.body, { color: palette.text.primary, textAlign: 'center', marginTop: 4 }]}>
              {fight.fighterA?.fullName} def. {fight.fighterB?.fullName} by {fight.result.method} R{fight.result.round} {fight.result.time}
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  header: { alignItems: 'center', padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  titleBadge: { color: '#F59E0B', fontWeight: '700', fontSize: 14, marginBottom: 4 },
  fighters: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.xl },
  fighterCard: { flex: 1, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, alignItems: 'center', marginHorizontal: 4 },
  avatar: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#1E1E32', alignItems: 'center', justifyContent: 'center' },
  predBadge: { marginTop: 8, paddingHorizontal: 14, paddingVertical: 4, borderRadius: 14 },
  predCard: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  predRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  factor: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  resultCard: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 1 },
});
