/** Predictions Components, Charts, Theme, Analytics, Errors, Skeletons, Utils, Accessibility */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { typography, spacing, radius, shadows } from '@/theme';
import type { FightPrediction, PredictionAccuracyStats, MonteCarloResult, PredictionOdds, PredictionFactor, FinishProbability } from '../types';

// ── WinProbabilityCard ──
export function WinProbabilityCard({ prediction, palette, onDetailPress }: { prediction: FightPrediction; palette: any; onDetailPress?: () => void }) {
  const probA = Math.round(prediction.probA * 100);
  const probB = Math.round(prediction.probB * 100);
  return (
    <View style={[s.winCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={s.fighters}>
        <View style={{ alignItems: 'center', flex: 1 }}>
          <Text style={[typography.title, { color: prediction.probA > 0.5 ? palette.text.primary : palette.text.tertiary, fontWeight: prediction.probA > 0.5 ? '700' : '400' }]}>{prediction.fighterA.fullName.split(' ').pop()}</Text>
          <Text style={[s.prob, { color: prediction.probA > 0.5 ? palette.primary[400] : palette.text.tertiary }]}>{probA}%</Text>
        </View>
        <View style={{ alignItems: 'center', paddingHorizontal: 12 }}>
          <Text style={[typography.body, { color: palette.text.tertiary }]}>VS</Text>
          <ConfidenceBadge level={prediction.confidence.level} />
        </View>
        <View style={{ alignItems: 'center', flex: 1 }}>
          <Text style={[typography.title, { color: prediction.probB > 0.5 ? palette.text.primary : palette.text.tertiary, fontWeight: prediction.probB > 0.5 ? '700' : '400' }]}>{prediction.fighterB.fullName.split(' ').pop()}</Text>
          <Text style={[s.prob, { color: prediction.probB > 0.5 ? palette.primary[400] : palette.text.tertiary }]}>{probB}%</Text>
        </View>
      </View>
      {onDetailPress && (
        <TouchableOpacity onPress={onDetailPress} style={{ marginTop: 12 }}>
          <Text style={[typography.caption, { color: palette.primary[400], textAlign: 'center' }]}>View full report →</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

// ── ConfidenceBadge ──
export function ConfidenceBadge({ level }: { level: string }) {
  const map: Record<string, { bg: string; label: string }> = {
    very_high: { bg: '#05966920', label: 'Very High' },
    high: { bg: '#10B98120', label: 'High' },
    medium: { bg: '#F59E0B20', label: 'Medium' },
    low: { bg: '#F9731620', label: 'Low' },
    coin_flip: { bg: '#6B728020', label: 'Coin Flip' },
  };
  const c = map[level] ?? map.coin_flip;
  return (
    <View style={[s.confBadge, { backgroundColor: c.bg }]}>
      <Text style={[typography.caption, { color: c.bg.replace('20', ''), fontWeight: '700' }]}>{c.label}</Text>
    </View>
  );
}

// ── FinishProbabilityBars ──
export function FinishProbabilityBars({ prediction, palette }: { prediction: FightPrediction; palette: any }) {
  return (
    <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>How the fight ends</Text>
      <ProbBar label="KO/TKO" prob={prediction.finish.koTko} color="#EF4444" palette={palette} />
      <ProbBar label="Submission" prob={prediction.finish.submission} color="#8B5CF6" palette={palette} />
      <ProbBar label="Decision" prob={prediction.finish.decision} color="#3B82F6" palette={palette} />
    </View>
  );
}

function ProbBar({ label, prob, color, palette }: { label: string; prob: number; color: string; palette: any }) {
  return (
    <View style={s.barRow}>
      <Text style={[typography.bodySmall, { color: palette.text.secondary, width: 80 }]}>{label}</Text>
      <View style={[s.barBg, { backgroundColor: '#1E1E32' }]}>
        <View style={[s.barFill, { width: `${Math.round(prob * 100)}%`, backgroundColor: color }]} />
      </View>
      <Text style={[typography.caption, { color: palette.text.primary, width: 42, textAlign: 'right' }]}>{Math.round(prob * 100)}%</Text>
    </View>
  );
}

// ── FactorsList ──
export function FactorsList({ factors, prediction, palette }: { factors: PredictionFactor[]; prediction: FightPrediction; palette: any }) {
  return (
    <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Key Factors</Text>
      {factors.map((f, i) => (
        <View key={i} style={s.factorRow}>
          <View style={{ flex: 1 }}>
            <Text style={[typography.bodySmall, { color: palette.text.primary }]}>{f.factor}</Text>
            <Text style={[typography.caption, { color: palette.text.tertiary }]}>{f.category} · favors {f.favors === 'fighter_a' ? prediction.fighterA.fullName.split(' ').pop() : prediction.fighterB.fullName.split(' ').pop()}</Text>
          </View>
          <Text style={[typography.bodySmall, { color: f.impact > 0 ? '#10B981' : '#EF4444', fontWeight: '700' }]}>{f.impact > 0 ? '+' : ''}{f.impact}</Text>
        </View>
      ))}
    </View>
  );
}

// ── MonteCarloCard ──
export function MonteCarloCard({ monteCarlo, palette, onPress }: { monteCarlo: MonteCarloResult; palette: any; onPress?: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.subtitle, { color: palette.text.primary }]}>Monte Carlo · {monteCarlo.simulations.toLocaleString()} sims</Text>
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 12 }}>
        <View style={{ alignItems: 'center' }}>
          <Text style={[s.mcProb, { color: palette.primary[400] }]}>{Math.round(monteCarlo.probA * 100)}%</Text>
          <Text style={[typography.caption, { color: palette.text.secondary }]}>Fighter A</Text>
        </View>
        <View style={{ alignItems: 'center' }}>
          <Text style={[typography.caption, { color: palette.text.tertiary }]}>95% CI</Text>
          <Text style={[typography.bodySmall, { color: palette.text.primary }]}>[{Math.round(monteCarlo.confidenceInterval95.lower * 100)}–{Math.round(monteCarlo.confidenceInterval95.upper * 100)}%]</Text>
        </View>
        <View style={{ alignItems: 'center' }}>
          <Text style={[s.mcProb, { color: '#8B5CF6' }]}>{Math.round(monteCarlo.probB * 100)}%</Text>
          <Text style={[typography.caption, { color: palette.text.secondary }]}>Fighter B</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// ── PredictionOddsCard ──
export function PredictionOddsCard({ odds, prediction, palette }: { odds: PredictionOdds; prediction: FightPrediction; palette: any }) {
  return (
    <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 8 }]}>Odds & Value</Text>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <View><Text style={[typography.mono, { color: palette.text.primary }]}>{odds.fighterA}</Text><Text style={[typography.caption, { color: odds.valueA && odds.valueA > 0 ? '#10B981' : palette.text.tertiary }]}>Value: {odds.valueA ? `+${Math.round(odds.valueA * 100)}%` : '--'}</Text></View>
        <View><Text style={[typography.mono, { color: palette.text.primary }]}>{odds.fighterB}</Text><Text style={[typography.caption, { color: odds.valueB && odds.valueB > 0 ? '#10B981' : palette.text.tertiary }]}>Value: {odds.valueB ? `+${Math.round(odds.valueB * 100)}%` : '--'}</Text></View>
      </View>
      <Text style={[typography.caption, { color: palette.text.tertiary, marginTop: 8 }]}>Source: {odds.source}</Text>
    </View>
  );
}

// ── AccuracyCard ──
export function AccuracyCard({ stats, palette }: { stats: PredictionAccuracyStats; palette: any }) {
  return (
    <View style={[s.accuracy, { backgroundColor: '#10B98110', borderColor: '#10B98130', marginHorizontal: spacing.lg, marginBottom: spacing.xl }]}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
        <Stat min label="Overall" value={`${Math.round(stats.overall * 100)}%`} />
        <Stat min label="Last 10" value={`${Math.round(stats.last10 * 100)}%`} />
        <Stat min label="High Conf" value={`${Math.round(stats.highConfidence * 100)}%`} />
        <Stat min label="Log Loss" value={stats.logLoss.toFixed(2)} />
      </View>
      <Text style={[typography.caption, { color: stats.calibrated ? '#10B981' : '#F59E0B', textAlign: 'center', marginTop: 8 }]}>{stats.calibrated ? '✓ Well calibrated' : '⚠ Needs calibration'}</Text>
    </View>
  );
}

function Stat({ label, value, min }: { label: string; value: string; min?: boolean }) {
  return <View style={{ alignItems: 'center', minWidth: 65 }}><Text style={[typography.title, { color: '#FFF' }]}>{value}</Text><Text style={[typography.caption, { color: '#9CA3AF' }]}>{label}</Text></View>;
}

// ── PredictionCard (compact) ──
export function PredictionCard({ prediction, palette, onPress }: { prediction: FightPrediction; palette: any; onPress: () => void }) {
  const winner = prediction.probA > 0.5 ? prediction.fighterA.fullName.split(' ').pop() : prediction.fighterB.fullName.split(' ').pop();
  const prob = Math.round(Math.max(prediction.probA, prediction.probB) * 100);
  return (
    <TouchableOpacity onPress={onPress} style={[s.predCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={{ flex: 1 }}>
        <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{prediction.fighterA.fullName.split(' ').pop()} vs {prediction.fighterB.fullName.split(' ').pop()}</Text>
        <Text style={[typography.caption, { color: palette.text.secondary }]}>{prediction.fighterA.record} · {prediction.fighterB.record}</Text>
      </View>
      <View style={{ alignItems: 'flex-end' }}>
        <Text style={[typography.title, { color: palette.primary[400] }]}>{winner} {prob}%</Text>
        <ConfidenceBadge level={prediction.confidence.level} />
      </View>
    </TouchableOpacity>
  );
}

// ── Skeleton + Empty ──
export function PredictionSkeleton() { return <View style={{ padding: spacing.lg, gap: 12 }}>{[1,2,3].map((i) => <View key={i} style={{ height: 160, backgroundColor: '#1A1A2E', borderRadius: radius.lg }} />)}</View>; }
export function PredictionEmpty({ message }: { message: string }) { return <View style={{ alignItems: 'center', paddingVertical: 60 }}><Text style={{ fontSize: 40 }}>🔮</Text><Text style={[typography.body, { color: '#9CA3AF', marginTop: 8 }]}>{message}</Text></View>; }

// ── Theme ──
export const predictionColors = {
  confidence: { very_high: '#059669', high: '#10B981', medium: '#F59E0B', low: '#F97316', coin_flip: '#6B7280' },
  finish: { ko: '#EF4444', sub: '#8B5CF6', dec: '#3B82F6' },
  correct: '#10B981', wrong: '#EF4444',
} as const;

// ── Accessibility ──
export const predictionLabels = {
  fight: (a: string, b: string) => `Prediction: ${a} vs ${b}`,
  confidence: (level: string, score: number) => `${level} confidence, ${score} out of 100`,
  factor: (f: string, impact: number) => `${f}: ${impact > 0 ? 'favors fighter A' : 'favors fighter B'}`,
};

// ── Analytics ──
export const predictionAnalytics = {
  predictionViewed: (fightId: string) => { if (__DEV__) console.log('[prediction] viewed', fightId); },
  saved: (fightId: string) => { if (__DEV__) console.log('[prediction] saved', fightId); },
  shared: (fightId: string) => { if (__DEV__) console.log('[prediction] shared', fightId); },
  accuracyViewed: () => { if (__DEV__) console.log('[prediction] accuracy'); },
};

// ── Errors ──
export function PredictionUnavailable({ message }: { message?: string }) { return <View style={{ alignItems: 'center', padding: 40 }}><Text style={{ fontSize: 40 }}>🔮</Text><Text style={[typography.body, { color: '#9CA3AF', marginTop: 8 }]}>{message || 'Prediction not available yet'}</Text></View>; }

const s = StyleSheet.create({
  winCard: { padding: spacing.xl, borderRadius: radius.xl, borderWidth: 0.5, marginBottom: spacing.lg, ...shadows.lg },
  fighters: { flexDirection: 'row', justifyContent: 'space-around', alignItems: 'center' },
  prob: { fontSize: 40, fontWeight: '800', marginTop: 4 },
  confBadge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, marginTop: 4 },
  card: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.lg },
  barRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  barBg: { flex: 1, height: 10, borderRadius: 5, overflow: 'hidden', marginHorizontal: 8 },
  barFill: { height: 10, borderRadius: 5 },
  factorRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  mcProb: { fontSize: 32, fontWeight: '800' },
  accuracy: { padding: spacing.lg, borderRadius: radius.lg, borderWidth: 1 },
  predCard: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginBottom: 8, borderRadius: radius.md, borderWidth: 0.5 },
});
