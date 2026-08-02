/** Animations — skeleton implementation (Reanimated in production) */
import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';

export function CountdownFlip({ value, unit }: { value: number; unit: string }) {
  return (
    <View style={as.flip}>
      <Text style={as.flipVal}>{String(value).padStart(2, '0')}</Text>
      <Text style={as.flipUnit}>{unit}</Text>
    </View>
  );
}

export function FightCardExpand({ children, expanded }: { children: React.ReactNode; expanded: boolean }) {
  return <View style={[as.expand, { maxHeight: expanded ? 500 : 80 }]}>{children}</View>;
}

export function LivePulse() {
  return (
    <View style={as.pulseWrap}>
      <View style={[as.pulseDot, { backgroundColor: '#EF4444' }]} />
      <Text style={as.pulseText}>LIVE</Text>
    </View>
  );
}

const as = StyleSheet.create({
  flip: { alignItems: 'center', paddingHorizontal: 4 },
  flipVal: { fontSize: 22, fontWeight: '700', color: '#FFF' },
  flipUnit: { fontSize: 10, color: '#9CA3AF', marginTop: 2 },
  expand: { overflow: 'hidden' },
  pulseWrap: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  pulseDot: { width: 8, height: 8, borderRadius: 4 },
  pulseText: { color: '#EF4444', fontSize: 12, fontWeight: '700', letterSpacing: 1 },
});
