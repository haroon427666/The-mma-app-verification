/** Predictions — Theme, Accessibility, Errors, Charts, Animations */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';

// ── Theme Tokens ──
export const predictionColors = {
  confidence: { very_high: '#059669', high: '#10B981', medium: '#F59E0B', low: '#F97316', coin_flip: '#6B7280' },
  finish: { ko: '#EF4444', sub: '#8B5CF6', dec: '#3B82F6' },
  factor: { positive: '#10B981', negative: '#EF4444', neutral: '#6B7280' },
  winProb: { bar: '#1E1E32', fill: '#3B82F6' },
  correct: '#10B981',
  wrong: '#EF4444',
} as const;

// ── Accessibility ──
export const predictionLabels = {
  fight: (a: string, b: string) => `Prediction: ${a} vs ${b}`,
  confidence: (score: number, level: string) => `Confidence: ${score} out of 100, ${level}`,
  finish: (type: string, prob: number) => `${type} probability: ${Math.round(prob * 100)} percent`,
  factor: (factor: string, impact: number) => `${factor}: ${impact > 0 ? 'positive' : 'negative'} impact`,
};

// ── Errors ──
export function PredictionUnavailable({ message = 'Prediction not available yet' }: { message?: string }) {
  return <View style={st.center}><Text style={st.icon}>🔮</Text><Text style={[typography.body, { color: '#9CA3AF', marginTop: 8 }]}>{message}</Text></View>;
}
export function NoPredictionsYet() {
  return <View style={st.center}><Text style={st.icon}>📊</Text><Text style={[typography.body, { color: '#9CA3AF', marginTop: 8 }]}>No predictions available yet. Check back when fight cards are announced.</Text></View>;
}

// ── Charts ──
export function MonteCarloChart({ probA, probB, confidenceInterval }: { probA: number; probB: number; confidenceInterval: { lower: number; upper: number } }) {
  return (
    <View style={st.chartWrap}>
      <Text style={[typography.subtitle, { color: '#FFF', marginBottom: spacing.md }]}>Monte Carlo Distribution</Text>
      <View style={st.distRow}>
        <View style={{ flex: probA }}><View style={[st.distBar, { height: `${Math.round(probA * 100)}%`, backgroundColor: '#3B82F6' }]} /></View>
        <View style={{ flex: probB }}><View style={[st.distBar, { height: `${Math.round(probB * 100)}%`, backgroundColor: '#8B5CF6' }]} /></View>
      </View>
      <Text style={[typography.caption, { color: '#6B7280', textAlign: 'center', marginTop: 8 }]}>95% CI: [{Math.round(confidenceInterval.lower * 100)}%, {Math.round(confidenceInterval.upper * 100)}%]</Text>
    </View>
  );
}

export function AccuracyChart({ overall, last10, highConfidence, calibrated }: { overall: number; last10: number; highConfidence: number; calibrated: boolean }) {
  return (
    <View style={st.chartWrap}>
      <Text style={[typography.subtitle, { color: '#FFF', marginBottom: spacing.md }]}>Prediction Accuracy</Text>
      {[{ label: 'Overall', v: overall }, { label: 'Last 10', v: last10 }, { label: 'High Conf', v: highConfidence }].map(({ label, v }, i) => (
        <View key={i} style={st.accBarRow}>
          <Text style={[typography.bodySmall, { color: '#9CA3AF', width: 70 }]}>{label}</Text>
          <View style={st.accBg}><View style={[st.accFill, { width: `${Math.round(v * 100)}%`, backgroundColor: calibrated ? '#10B981' : '#3B82F6' }]} /></View>
          <Text style={[typography.mono, { color: '#FFF', width: 42, textAlign: 'right' }]}>{Math.round(v * 100)}%</Text>
        </View>
      ))}
    </View>
  );
}

export function CalibrationChart() {
  return (
    <View style={st.chartWrap}>
      <Text style={[typography.subtitle, { color: '#FFF', marginBottom: spacing.md }]}>Calibration Curve</Text>
      <View style={[st.chartPlaceholder, { backgroundColor: '#1A1A2E', height: 160 }]}>
        <Text style={{ color: '#6B7280' }}>Calibration plot</Text>
      </View>
    </View>
  );
}

// ── Animations ──
export function ConfidenceGauge({ score }: { score: number }) {
  const color = score >= 85 ? '#059669' : score >= 70 ? '#10B981' : score >= 60 ? '#F59E0B' : '#6B7280';
  return (
    <View style={st.gauge}>
      <View style={[st.gaugeTrack, { backgroundColor: '#1E1E32' }]}>
        <View style={[st.gaugeFill, { width: `${score}%`, backgroundColor: color }]} />
      </View>
      <Text style={[typography.title, { color, fontWeight: '700', marginTop: 4 }]}>{score}/100</Text>
    </View>
  );
}

export function ProbabilityReveal({ prob }: { prob: number }) {
  return (
    <View style={st.reveal}>
      <Text style={{ fontSize: 48, fontWeight: '800', color: '#3B82F6' }}>{Math.round(prob * 100)}%</Text>
    </View>
  );
}

const st = StyleSheet.create({
  center: { alignItems: 'center', paddingVertical: 60 }, icon: { fontSize: 48 },
  chartWrap: { marginBottom: spacing.xl },
  distRow: { flexDirection: 'row', height: 120, gap: 4, alignItems: 'flex-end' },
  distBar: { width: '100%', borderTopLeftRadius: 4, borderTopRightRadius: 4 },
  accBarRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  accBg: { flex: 1, height: 14, backgroundColor: '#1E1E32', borderRadius: 7, overflow: 'hidden', marginHorizontal: 8 },
  accFill: { height: 14, borderRadius: 7 },
  chartPlaceholder: { borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center' },
  gauge: { alignItems: 'center', padding: spacing.lg },
  gaugeTrack: { width: '100%', height: 12, borderRadius: 6, overflow: 'hidden' },
  gaugeFill: { height: 12, borderRadius: 6 },
  reveal: { alignItems: 'center', padding: spacing.xl },
});
