/** Skeletons + Error states */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { spacing, radius } from '@/theme';

const SS = { backgroundColor: '#1A1A2E', borderRadius: radius.sm };

export function FighterCardSkeleton() {
  return <View style={sk.card}>{[1,2,3,4].map((i) => <View key={i} style={[sk.block, SS]} />)}</View>;
}

export function ProfileSkeleton() {
  return (
    <View style={{ padding: spacing.lg }}>
      <View style={[sk.banner, SS]} />
      {[1,2,3,4,5,6].map((i) => <View key={i} style={[sk.line, SS]} />)}
    </View>
  );
}

export function EmptyState({ message, palette }: { message: string; palette?: any }) {
  return (
    <View style={sk.center}>
      <Text style={{ fontSize: 40 }}>🔍</Text>
      <Text style={{ color: '#9CA3AF', marginTop: 8, fontSize: 14 }}>{message}</Text>
    </View>
  );
}

export function ErrorState({ message, palette, onRetry }: { message?: string; palette?: any; onRetry?: () => void }) {
  return (
    <View style={sk.center}>
      <Text style={{ fontSize: 40 }}>⚠️</Text>
      <Text style={{ color: '#9CA3AF', marginTop: 8, fontSize: 14 }}>{message || 'Something went wrong'}</Text>
      {onRetry && <TouchableOpacity onPress={onRetry} style={{ marginTop: 15, padding: 10, backgroundColor: '#3B82F6', borderRadius: 8 }}><Text style={{ color: '#FFF' }}>Retry</Text></TouchableOpacity>}
    </View>
  );
}

const sk = StyleSheet.create({
  card: { padding: spacing.lg, gap: 12 },
  block: { height: 72, borderRadius: radius.md },
  banner: { height: 200, borderRadius: radius.lg, marginBottom: spacing.lg },
  line: { height: 16, marginBottom: 10, borderRadius: radius.sm, width: '70%' },
  center: { alignItems: 'center', paddingVertical: 60 },
});
