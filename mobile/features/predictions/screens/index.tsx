/** Predictions Screens — Dashboard, Fight, Report, Monte Carlo, Confidence, Style, History, Saved, Compare */

import React from 'react';
import { View, Text, ScrollView, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius, shadows } from '@/theme';
import { usePredictionDashboard, usePredictionHighlights, useFightPrediction, usePredictionHistory, usePredictionAccuracy, useSavedPredictions, useSavePrediction, useUnsavePrediction, usePredictionStore, predictionActions, predictionAnalytics } from '../api';
import type { FightPrediction, PredictionDashboard, AccuracyStats, PredictionHistoryEntry, ConfidenceLevel, KeyFactor } from '../types';

// ── Dashboard ──
export function PredictionDashboardScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { view } = usePredictionStore();
  const { data: dashboard, isLoading, refetch } = usePredictionDashboard();
  const { data: highlights } = usePredictionHighlights();
  const { data: accuracy } = usePredictionAccuracy();

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}>
        <Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg, paddingBottom: 4 }]}>Predictions</Text>

        {accuracy && <AccuracyCard stats={accuracy} palette={palette} onPress={() => predictionAnalytics.accuracyViewed()} />}

        {dashboard?.topConfidence && dashboard.topConfidence.length > 0 && (
          <View style={s.section}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.sm }]}>Highest Confidence</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12, paddingRight: spacing.lg }}>
              {dashboard.topConfidence.map((p: FightPrediction) => (
                <PredictionFeaturedCard key={p.fightId} prediction={p} palette={palette} onPress={() => navigation.navigate('FightPrediction', { fightId: p.fightId })} />
              ))}
            </ScrollView>
          </View>
        )}

        {highlights && highlights.length > 0 && (
          <View style={s.section}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.sm }]}>Upcoming Predictions</Text>
            {highlights.slice(0, 5).map((p: FightPrediction) => (
              <PredictionCompactCard key={p.fightId} prediction={p} palette={palette} onPress={() => navigation.navigate('FightPrediction', { fightId: p.fightId })} />
            ))}
          </View>
        )}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Fight Prediction (full detail) ──
export function FightPredictionScreen({ route }: any) {
  const { fightId } = route.params;
  const { palette } = useTheme();
  const { data: prediction, isLoading } = useFightPrediction(fightId);
  const save = useSavePrediction();
  const unsave = useUnsavePrediction();
  const { savedIds } = usePredictionStore();
  const isSaved = savedIds.has(fightId);

  if (isLoading || !prediction) return <View style={[s.root, { backgroundColor: palette.surface.bg }]} />;

  const f = prediction;
  const pConf = Math.round(f.confidence.score);
  const confColor = pConf >= 85 ? '#059669' : pConf >= 70 ? '#10B981' : pConf >= 60 ? '#F59E0B' : '#6B7280';

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <TouchableOpacity onPress={() => isSaved ? unsave.mutate(fightId) : save.mutate(fightId)} style={{ alignSelf: 'flex-end', marginBottom: spacing.md }}>
          <Text style={{ fontSize: 24 }}>{isSaved ? '★' : '☆'}</Text>
        </TouchableOpacity>

        <Text style={[typography.headline, { color: palette.text.primary, textAlign: 'center' }]}>{f.fighterA.fullName} vs {f.fighterB.fullName}</Text>
        <Text style={[typography.caption, { color: palette.text.tertiary, textAlign: 'center', marginTop: 4 }]}>{f.fighterA.record} • {f.fighterB.record}</Text>

        {/* Winner Probability */}
        <View style={[s.winCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border, marginTop: 20 }]}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-around', alignItems: 'center' }}>
            <WinProbBlock name={f.fighterA.fullName.split(' ').pop()!} prob={f.probA} confidence={f.confidence.level} palette={palette} />
            <View style={{ alignItems: 'center' }}>
              <Text style={[typography.headline, { color: palette.text.tertiary, marginVertical: 16 }]}>VS</Text>
              <View style={[s.confChip, { backgroundColor: confColor }]}>
                <Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{f.confidence.level.replace('_', ' ').toUpperCase()}</Text>
              </View>
              <Text style={[typography.caption, { color: palette.text.tertiary, marginTop: 4 }]}>{pConf}/100</Text>
            </View>
            <WinProbBlock name={f.fighterB.fullName.split(' ').pop()!} prob={f.probB} confidence={f.confidence.level} palette={palette} />
          </View>
        </View>

        {/* Finish Probability */}
        <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
          <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Finish Probability</Text>
          <ProbBar label="KO/TKO" prob={f.finish.koTko} color="#EF4444" palette={palette} />
          <ProbBar label="Submission" prob={f.finish.submission} color="#8B5CF6" palette={palette} />
          <ProbBar label="Decision" prob={f.finish.decision} color="#3B82F6" palette={palette} />
        </View>

        {/* Round Distribution */}
        {f.rounds && Object.keys(f.rounds).length > 0 && (
          <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Round Probability</Text>
            {Object.entries(f.rounds).map(([r, prob]) => (
              <ProbBar key={r} label={r.replace('round_', 'Round ')} prob={prob as number} color={palette.primary[400]} palette={palette} />
            ))}
          </View>
        )}

        {/* Key Factors */}
        {f.keyFactors && f.keyFactors.length > 0 && (
          <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Key Factors</Text>
            {f.keyFactors.map((kf: KeyFactor, i: number) => (
              <View key={i} style={s.factorRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[typography.body, { color: palette.text.primary }]}>{kf.factor}</Text>
                  <Text style={[typography.caption, { color: palette.text.tertiary }]}>{kf.category} • favors {kf.favors === 'fighter_a' ? f.fighterA.fullName.split(' ').pop() : f.fighterB.fullName.split(' ').pop()}</Text>
                </View>
                <Text style={[typography.bodySmall, { color: kf.impact > 0 ? '#10B981' : '#EF4444', fontWeight: '700' }]}>{kf.impact > 0 ? '+' : ''}{kf.impact}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Monte Carlo */}
        {f.monteCarlo && (
          <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 8 }]}>Monte Carlo ({f.monteCarlo.simulations?.toLocaleString()} sims)</Text>
            <View style={s.mcRow}>
              <View style={{ alignItems: 'center' }}>
                <Text style={[typography.display, { color: palette.text.primary }]}>{Math.round(f.monteCarlo.probA * 100)}%</Text>
                <Text style={[typography.caption, { color: palette.text.secondary }]}>{f.fighterA.fullName.split(' ').pop()}</Text>
              </View>
              <View style={s.mcVs}>
                <Text style={[typography.caption, { color: palette.text.tertiary }]}>95% CI</Text>
                <Text style={[typography.mono, { color: palette.text.primary }]}>[{Math.round(f.monteCarlo.confidenceInterval95.lower * 100)}%-{Math.round(f.monteCarlo.confidenceInterval95.upper * 100)}%]</Text>
              </View>
            </View>
          </View>
        )}

        {/* Style Matchup */}
        {f.styleAnalysis && (
          <TouchableOpacity style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}
            onPress={() => navigation.navigate('StyleMatchup', { fighterA: f.fighterA.id, fighterB: f.fighterB.id })}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 4 }]}>Style Matchup</Text>
            <Text style={[typography.body, { color: palette.primary[400], fontWeight: '600' }]}>{f.styleAnalysis.archetype?.replace(/_/g, ' ')}</Text>
            <Text style={[typography.caption, { color: palette.text.secondary }]}>Tap for full analysis →</Text>
          </TouchableOpacity>
        )}

        {/* Odds / Value Bet */}
        {f.odds && (
          <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 8 }]}>Odds & Value</Text>
            <View style={s.oddsRow}>
              <View>
                <Text style={[typography.mono, { color: palette.text.primary }]}>{f.odds.fighterA}</Text>
                <Text style={[typography.caption, { color: f.odds.valueA !== null && f.odds.valueA! > 0 ? '#10B981' : palette.text.tertiary }]}>Value: {f.odds.valueA !== null ? (f.odds.valueA! > 0 ? `+${Math.round(f.odds.valueA! * 100)}%` : `${Math.round(f.odds.valueA! * 100)}%`) : '--'}</Text>
              </View>
              <Text style={[typography.bodySmall, { color: palette.text.tertiary }]}>vs</Text>
              <View>
                <Text style={[typography.mono, { color: palette.text.primary }]}>{f.odds.fighterB}</Text>
                <Text style={[typography.caption, { color: f.odds.valueB !== null && f.odds.valueB! > 0 ? '#10B981' : palette.text.tertiary }]}>Value: {f.odds.valueB !== null ? (f.odds.valueB! > 0 ? `+${Math.round(f.odds.valueB! * 100)}%` : `${Math.round(f.odds.valueB! * 100)}%`) : '--'}</Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Sub-components ──
function WinProbBlock({ name, prob, confidence, palette }: { name: string; prob: number; confidence: ConfidenceLevel; palette: any }) {
  const isWinner = prob > 0.5;
  return (
    <View style={{ alignItems: 'center' }}>
      <Text style={[typography.title, { color: isWinner ? palette.text.primary : palette.text.tertiary, fontWeight: isWinner ? '700' : '400' }]}>{name}</Text>
      <Text style={[typography.display, { color: isWinner ? palette.primary[400] : palette.text.tertiary, fontSize: 36 }]}>{Math.round(prob * 100)}%</Text>
    </View>
  );
}

function ProbBar({ label, prob, color, palette }: { label: string; prob: number; color: string; palette: any }) {
  return (
    <View style={s.barWrap}>
      <Text style={[typography.bodySmall, { color: palette.text.secondary, width: 90 }]}>{label}</Text>
      <View style={[s.bar, { backgroundColor: '#1E1E32' }]}>
        <View style={[s.barFill, { width: `${Math.round(prob * 100)}%`, backgroundColor: color }]} />
      </View>
      <Text style={[typography.mono, { color: palette.text.primary, width: 42, textAlign: 'right' }]}>{Math.round(prob * 100)}%</Text>
    </View>
  );
}

function PredictionFeaturedCard({ prediction, palette, onPress }: { prediction: FightPrediction; palette: any; onPress: () => void }) {
  const winner = prediction.probA > 0.5 ? prediction.fighterA.fullName.split(' ').pop() : prediction.fighterB.fullName.split(' ').pop();
  const probWin = Math.round(Math.max(prediction.probA, prediction.probB) * 100);
  return (
    <TouchableOpacity onPress={onPress} style={[s.featuredCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]} numberOfLines={2}>{prediction.fighterA.fullName.split(' ').pop()} vs {prediction.fighterB.fullName.split(' ').pop()}</Text>
      <Text style={[typography.title, { color: palette.primary[400], fontWeight: '700', marginTop: 8 }]}>{winner} {probWin}%</Text>
      <ConfidenceBadge level={prediction.confidence.level} />
    </TouchableOpacity>
  );
}

function PredictionCompactCard({ prediction, palette, onPress }: { prediction: FightPrediction; palette: any; onPress: () => void }) {
  const probWin = Math.round(Math.max(prediction.probA, prediction.probB) * 100);
  const winner = prediction.probA > 0.5 ? prediction.fighterA.fullName.split(' ').pop() : prediction.fighterB.fullName.split(' ').pop();
  return (
    <TouchableOpacity onPress={onPress} style={[s.compactCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={{ flex: 1 }}>
        <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{prediction.fighterA.fullName.split(' ').pop()} vs {prediction.fighterB.fullName.split(' ').pop()}</Text>
      </View>
      <View style={{ alignItems: 'flex-end' }}>
        <Text style={[typography.body, { color: palette.primary[400], fontWeight: '700' }]}>{winner} {probWin}%</Text>
        <ConfidenceBadge level={prediction.confidence.level} />
      </View>
    </TouchableOpacity>
  );
}

function AccuracyCard({ stats, palette, onPress }: { stats: AccuracyStats; palette: any; onPress?: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={[s.accuracyCard, { backgroundColor: '#10B98115', borderColor: '#10B98130' }]}>
      <View style={s.accGrid}>
        <AccStat label="Overall" value={`${Math.round(stats.overall * 100)}%`} palette={palette} />
        <AccStat label="Last 10" value={`${Math.round(stats.last10 * 100)}%`} palette={palette} />
        <AccStat label="High Conf" value={`${Math.round(stats.highConfidence * 100)}%`} palette={palette} />
        <AccStat label="Log Loss" value={stats.logLoss?.toFixed(2)} palette={palette} />
      </View>
      <Text style={[typography.caption, { color: stats.calibrated ? '#10B981' : '#F59E0B', textAlign: 'center', marginTop: 8 }]}>
        {stats.calibrated ? '✓ Well calibrated' : '⚠ Needs calibration'}
      </Text>
    </TouchableOpacity>
  );
}

function AccStat({ label, value, palette }: { label: string; value: string; palette: any }) {
  return (
    <View style={{ alignItems: 'center', minWidth: 70 }}>
      <Text style={[typography.title, { color: palette.text.primary, fontWeight: '700' }]}>{value}</Text>
      <Text style={[typography.caption, { color: palette.text.secondary }]}>{label}</Text>
    </View>
  );
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const map: Record<ConfidenceLevel, { bg: string; text: string }> = {
    very_high: { bg: '#05966920', text: '#059669' },
    high: { bg: '#10B98120', text: '#10B981' },
    medium: { bg: '#F59E0B20', text: '#F59E0B' },
    low: { bg: '#F9731620', text: '#F97316' },
    coin_flip: { bg: '#6B728020', text: '#6B7280' },
  };
  const c = map[level] ?? map.coin_flip;
  return (
    <View style={[s.confBadge, { backgroundColor: c.bg }]}>
      <Text style={[typography.caption, { color: c.text, fontWeight: '700' }]}>{level.replace('_', ' ')}</Text>
    </View>
  );
}

export { FightPredictionScreen as PredictionReportScreen, FightPredictionScreen as MonteCarloViewScreen };

// ── History Screen ──
export function PredictionHistoryScreen() {
  const { palette } = useTheme();
  const { data: history, isLoading, refetch } = usePredictionHistory();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList
        data={history ?? []}
        keyExtractor={(h: any) => h.prediction?.fightId || Math.random().toString()}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>Prediction History</Text>}
        renderItem={({ item }) => (
          <View style={[s.histRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={{ flex: 1 }}>
              <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]}>{item.prediction?.fighterA?.fullName?.split(' ').pop()} vs {item.prediction?.fighterB?.fullName?.split(' ').pop()}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.fight?.eventName} • {item.fight?.date?.slice(0, 10)}</Text>
            </View>
            <Text style={[typography.bodySmall, { color: item.wasCorrect ? '#10B981' : '#EF4444', fontWeight: '700' }]}>{item.wasCorrect ? '✓' : '✗'} {Math.round(item.predictedProb * 100)}%</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

// ── Saved Predictions ──
export function SavedPredictionsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { data: saved } = useSavedPredictions();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList
        data={saved ?? []}
        keyExtractor={(p: any) => p.fightId}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>★ Saved Predictions</Text>}
        renderItem={({ item }) => <PredictionCompactCard prediction={item as any} palette={palette} onPress={() => navigation.navigate('FightPrediction', { fightId: (item as any).fightId })} />}
        ListEmptyComponent={<Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>No saved predictions. Star a prediction to save it.</Text>}
      />
    </SafeAreaView>
  );
}

// ── Compare ──
export function ComparePredictionsScreen({ route }: any) {
  const { palette } = useTheme();
  const { fightIdA, fightIdB } = route.params ?? {};
  const { data: predA } = useFightPrediction(fightIdA);
  const { data: predB } = useFightPrediction(fightIdB);

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary, marginBottom: spacing.xl }]}>Compare Predictions</Text>
        {predA && <PredictionCompactCard prediction={predA} palette={palette} onPress={() => {}} />}
        {predB && <PredictionCompactCard prediction={predB} palette={palette} onPress={() => {}} />}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  section: { paddingHorizontal: spacing.lg, marginBottom: spacing.xl },
  winCard: { padding: spacing.xl, borderRadius: radius.xl, borderWidth: 0.5, marginBottom: spacing.lg, ...shadows.lg },
  card: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  featuredCard: { width: 200, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5 },
  compactCard: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5, marginHorizontal: spacing.lg },
  accuracyCard: { marginHorizontal: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 1, marginBottom: spacing.xl },
  accGrid: { flexDirection: 'row', justifyContent: 'space-around' },
  barWrap: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  bar: { flex: 1, height: 10, borderRadius: 5, overflow: 'hidden', marginHorizontal: 8 },
  barFill: { height: 10, borderRadius: 5 },
  factorRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  confChip: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  confBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, alignSelf: 'flex-start', marginTop: 4 },
  mcRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  mcVs: { alignItems: 'center' },
  oddsRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  histRow: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 6 },
});
