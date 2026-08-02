/** Predictions Screens — Dashboard, Fight, Report, Monte Carlo, History, Saved, Compare */

import React from 'react';
import { View, Text, ScrollView, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { typography, spacing, radius, shadows } from '@/theme';
import { useTheme } from '@/hooks/useTheme';
import { usePredictionDashboard, usePredictionHighlights, useFightPrediction, usePredictionHistory, usePredictionAccuracy, useSavedPredictions, useSavePrediction, useUnsavePrediction, useMonteCarlo, usePredictionFactors, usePredictionOdds } from '../hooks/usePredictions';
import { usePredictionsStore, predictionsActions } from '../stores/predictions.store';
import { PredictionCard, WinProbabilityCard, ConfidenceBadge, FinishProbabilityBars, FactorsList, MonteCarloCard, PredictionOddsCard, AccuracyCard, PredictionSkeleton, PredictionEmpty } from '../components/PredictionsComponents';
import type { FightPrediction } from '../types';

// ── Dashboard ──
export function PredictionsDashboardScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { view } = usePredictionsStore();
  const { data: dashboard, isLoading, refetch } = usePredictionDashboard();
  const { data: highlights } = usePredictionHighlights();
  const { data: accuracy } = usePredictionAccuracy();

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}>
        <Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg, paddingBottom: 4 }]}>Predictions</Text>
        {accuracy && <AccuracyCard stats={accuracy} palette={palette} />}
        {highlights && highlights.length > 0 && (
          <View style={s.section}>
            <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.sm }]}>Top Predictions</Text>
            {highlights.slice(0, 6).map((p) => (
              <PredictionCard key={p.fightId} prediction={p} palette={palette} onPress={() => navigation.navigate('FightPrediction', { fightId: p.fightId })} />
            ))}
          </View>
        )}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Fight Prediction ──
export function FightPredictionScreen({ route, navigation }: any) {
  const { fightId } = route.params;
  const { palette } = useTheme();
  const { data: prediction, isLoading } = useFightPrediction(fightId);
  const { data: monteCarlo } = useMonteCarlo(fightId);
  const { data: factors } = usePredictionFactors(fightId);
  const { data: odds } = usePredictionOdds(fightId);
  const saveMut = useSavePrediction();
  const unsaveMut = useUnsavePrediction();
  const { savedIds } = usePredictionsStore();
  const isSaved = savedIds.has(fightId);

  if (isLoading || !prediction) return <PredictionSkeleton />;

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <TouchableOpacity onPress={() => isSaved ? unsaveMut.mutate(fightId) : saveMut.mutate(fightId)} style={{ alignSelf: 'flex-end' }}>
          <Text style={{ fontSize: 28, color: isSaved ? '#F59E0B' : palette.text.tertiary }}>{isSaved ? '★' : '☆'}</Text>
        </TouchableOpacity>
        <WinProbabilityCard prediction={prediction} palette={palette} onDetailPress={() => navigation.navigate('PredictionReport', { fightId })} />
        <FinishProbabilityBars prediction={prediction} palette={palette} />
        {odds && <PredictionOddsCard odds={odds} prediction={prediction} palette={palette} />}
        {factors && <FactorsList factors={factors} prediction={prediction} palette={palette} />}
        {monteCarlo && <MonteCarloCard monteCarlo={monteCarlo} palette={palette} onPress={() => navigation.navigate('MonteCarlo', { fightId })} />}
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Report + Monte Carlo + History + Saved + Compare ──
export function PredictionReportScreen({ route }: any) {
  const { fightId } = route.params;
  const { palette } = useTheme();
  const { data: prediction } = useFightPrediction(fightId);
  const { data: factors } = usePredictionFactors(fightId);
  if (!prediction) return <PredictionSkeleton />;
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary, textAlign: 'center' }]}>{prediction.fighterA.fullName} vs {prediction.fighterB.fullName}</Text>
        <Text style={[typography.caption, { color: palette.text.tertiary, textAlign: 'center', marginBottom: spacing.xl }]}>Full Prediction Report</Text>
        <WinProbabilityCard prediction={prediction} palette={palette} />
        <FinishProbabilityBars prediction={prediction} palette={palette} />
        {factors && <FactorsList factors={factors} prediction={prediction} palette={palette} />}
        {prediction.styleMatchup && (
          <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.subtitle, { color: palette.text.primary }]}>Style Matchup</Text>
            <Text style={[typography.body, { color: palette.primary[400] }]}>{prediction.styleMatchup.archetype}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

export function MonteCarloScreen({ route }: any) {
  const { fightId } = route.params;
  const { palette } = useTheme();
  const { data: mc } = useMonteCarlo(fightId);
  if (!mc) return <PredictionSkeleton />;
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary }]}>Monte Carlo Simulation</Text>
        <Text style={[typography.caption, { color: palette.text.secondary }]}>{mc.simulations.toLocaleString()} simulations</Text>
        <MonteCarloCard monteCarlo={mc} palette={palette} />
        <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border, marginTop: spacing.lg }]}>
          <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Round Distribution</Text>
          {Object.entries(mc.roundDistribution).map(([r, v]) => (
            <View key={r} style={s.barRow}>
              <Text style={[typography.bodySmall, { color: palette.text.secondary, width: 60 }]}>{r.replace('round_', 'R')}</Text>
              <View style={[s.barBg, { backgroundColor: '#1E1E32' }]}>
                <View style={[s.bar, { width: `${Math.round(v * 100)}%`, backgroundColor: palette.primary[400] }]} />
              </View>
              <Text style={[typography.caption, { color: palette.text.primary, width: 42, textAlign: 'right' }]}>{Math.round(v * 100)}%</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

export function PredictionHistoryScreen() {
  const { palette } = useTheme();
  const { data: history, isLoading, refetch } = usePredictionHistory();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList data={history ?? []} keyExtractor={(h) => h.id} refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>Prediction History</Text>}
        renderItem={({ item }) => (
          <View style={[s.histRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={{ flex: 1 }}>
              <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]}>{item.prediction?.fighterA?.fullName?.split(' ').pop()} vs {item.prediction?.fighterB?.fullName?.split(' ').pop()}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.actual?.method} R{item.actual?.round}</Text>
            </View>
            <Text style={[typography.body, { color: item.correct ? '#10B981' : '#EF4444', fontWeight: '700' }]}>{item.correct ? '✓' : '✗'} {Math.round(item.predictedProb * 100)}%</Text>
          </View>
        )}
        ListEmptyComponent={<PredictionEmpty message="No prediction history yet" />}
      />
    </SafeAreaView>
  );
}

export function SavedPredictionsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { data: saved } = useSavedPredictions();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList data={saved ?? []} keyExtractor={(p) => p.fightId}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>★ Saved Predictions</Text>}
        renderItem={({ item }) => <PredictionCard prediction={item} palette={palette} onPress={() => navigation.navigate('FightPrediction', { fightId: item.fightId })} />}
        ListEmptyComponent={<PredictionEmpty message="No saved predictions. Star a prediction to save it." />}
      />
    </SafeAreaView>
  );
}

export function ComparePredictionsScreen({ route, navigation }: any) {
  const { fightIdA, fightIdB } = route.params;
  const { palette } = useTheme();
  const { data: predA } = useFightPrediction(fightIdA);
  const { data: predB } = fightIdB ? useFightPrediction(fightIdB) : { data: null };

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary, marginBottom: spacing.xl }]}>Compare Predictions</Text>
        {predA && <PredictionCard prediction={predA} palette={palette} onPress={() => {}} />}
        {predB && <PredictionCard prediction={predB} palette={palette} onPress={() => {}} />}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  section: { paddingHorizontal: spacing.lg, marginBottom: spacing.xl },
  card: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  barRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  barBg: { flex: 1, height: 10, borderRadius: 5, overflow: 'hidden', marginHorizontal: 8, backgroundColor: '#1E1E32' },
  bar: { height: 10, borderRadius: 5 },
  histRow: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 6 },
});
