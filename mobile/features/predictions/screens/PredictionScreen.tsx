/** Prediction screen — full fight prediction with Monte Carlo, method, round */

import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import api from '@/services/api';
import { typography, spacing, radius } from '@/theme';
import type { Prediction } from '@/features/models';

export function PredictionScreen({ route }: any) {
  const { palette } = useTheme();
  const { fightId } = route.params;
  const { data: prediction, isLoading } = useQuery<Prediction>({
    queryKey: ['prediction', fightId],
    queryFn: async () => { const { data } = await api.get(`/v1/predictions/fight/${fightId}`); return data; },
  });

  if (isLoading || !prediction) return <View style={[st.root, { backgroundColor: palette.surface.bg }]} />;
  const f = prediction;
  const probWin = Math.max(f.probA, f.probB);
  const winner = f.probA > 0.5 ? f.fighterA : f.fighterB;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary, textAlign: 'center' }]}>{f.fighterA} vs {f.fighterB}</Text>

        <View style={[st.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border, marginTop: 20 }]}>
          <Text style={[typography.subtitle, { color: palette.text.primary, textAlign: 'center' }]}>Winner Prediction</Text>
          <Text style={[st.bigText, { color: palette.primary[400] }]}>{winner}</Text>
          <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 24, marginTop: 8 }}>
            <View style={{ alignItems: 'center' }}><Text style={[typography.display, { color: palette.text.primary }]}>{Math.round(f.probA * 100)}%</Text><Text style={[typography.caption, { color: palette.text.secondary }]}>{f.fighterA.split(' ').pop()}</Text></View>
            <Text style={[typography.title, { color: palette.text.tertiary, marginTop: 20 }]}>vs</Text>
            <View style={{ alignItems: 'center' }}><Text style={[typography.display, { color: palette.text.primary }]}>{Math.round(f.probB * 100)}%</Text><Text style={[typography.caption, { color: palette.text.secondary }]}>{f.fighterB.split(' ').pop()}</Text></View>
          </View>
          <View style={[st.confBadge, { backgroundColor: f.confidence.level === 'high' ? '#10B981' : f.confidence.level === 'very_high' ? '#059669' : '#6B7280' }]}>
            <Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>Confidence: {Math.round(f.confidence.score)}/100 • {f.confidence.level.replace('_', ' ')}</Text>
          </View>
        </View>

        <View style={[st.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
          <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Finish Probability</Text>
          <View style={st.barRow}><Text style={[typography.body, { color: palette.text.secondary, width: 90 }]}>KO/TKO</Text><View style={[st.bar, { flex: f.finish.koTko }]}><View style={[st.barFill, { width: `${Math.round(f.finish.koTko * 100)}%`, backgroundColor: '#EF4444' }]} /></View><Text style={[typography.mono, { color: palette.text.primary, width: 40 }]}>{Math.round(f.finish.koTko * 100)}%</Text></View>
          <View style={st.barRow}><Text style={[typography.body, { color: palette.text.secondary, width: 90 }]}>Submission</Text><View style={[st.bar, { flex: f.finish.submission }]}><View style={[st.barFill, { width: `${Math.round(f.finish.submission * 100)}%`, backgroundColor: '#8B5CF6' }]} /></View><Text style={[typography.mono, { color: palette.text.primary, width: 40 }]}>{Math.round(f.finish.submission * 100)}%</Text></View>
          <View style={st.barRow}><Text style={[typography.body, { color: palette.text.secondary, width: 90 }]}>Decision</Text><View style={[st.bar, { flex: f.finish.decision }]}><View style={[st.barFill, { width: `${Math.round(f.finish.decision * 100)}%`, backgroundColor: '#3B82F6' }]} /></View><Text style={[typography.mono, { color: palette.text.primary, width: 40 }]}>{Math.round(f.finish.decision * 100)}%</Text></View>
        </View>

        {f.rounds && (
          <View style={[st.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Round Probability</Text>
            {Object.entries(f.rounds).map(([round, prob]) => (
              <View key={round} style={st.barRow}>
                <Text style={[typography.body, { color: palette.text.secondary, width: 70 }]}>{round.replace('_', ' ')}</Text>
                <View style={st.bar}><View style={[st.barFill, { width: `${Math.round((prob as number) * 100)}%`, backgroundColor: palette.primary[500] }]} /></View>
                <Text style={[typography.mono, { color: palette.text.primary, width: 40 }]}>{Math.round((prob as number) * 100)}%</Text>
              </View>
            ))}
          </View>
        )}

        {f.keyFactors && f.keyFactors.length > 0 && (
          <View style={[st.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Key Factors</Text>
            {f.keyFactors.map((kf, i) => (
              <View key={i} style={st.factorRow}>
                <Text style={[typography.body, { color: palette.text.primary }]}>{kf.factor}</Text>
                <Text style={[typography.bodySmall, { color: kf.impact > 0 ? '#10B981' : '#EF4444', fontWeight: '700' }]}>{kf.impact > 0 ? '+' : ''}{kf.impact}</Text>
              </View>
            ))}
          </View>
        )}

        {f.styleAnalysis && (
          <View style={[st.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 8 }]}>Style Matchup</Text>
            <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{f.styleAnalysis.archetype?.replace(/_/g, ' ')}</Text>
            <Text style={[typography.bodySmall, { color: palette.text.secondary, marginTop: 4 }]}>Striker: {f.styleAnalysis.strikerAdvantage} • Grappler: {f.styleAnalysis.grapplerAdvantage}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  card: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  bigText: { fontSize: 28, fontWeight: '800', textAlign: 'center', marginTop: 8 },
  confBadge: { alignSelf: 'center', marginTop: 12, paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20 },
  barRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  bar: { flex: 1, height: 10, backgroundColor: '#1E1E32', borderRadius: 5, marginHorizontal: 8, overflow: 'hidden' },
  barFill: { height: 10, borderRadius: 5 },
  factorRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
});
