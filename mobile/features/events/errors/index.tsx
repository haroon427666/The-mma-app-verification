/** Error components — domain-specific error states */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { typography, spacing } from '@/theme';

export function EventNotFound({ onBack }: { onBack?: () => void }) {
  return (
    <View style={es.center}>
      <Text style={{ fontSize: 48 }}>🔍</Text>
      <Text style={[typography.title, { color: '#9CA3AF', marginTop: 12 }]}>Event not found</Text>
      <Text style={[typography.bodySmall, { color: '#6B7280', marginTop: 4, textAlign: 'center' }]}>This event may have been removed or the link is invalid.</Text>
      {onBack && <TouchableOpacity onPress={onBack} style={es.btn}><Text style={{ color: '#FFF', fontWeight: '600' }}>Go back</Text></TouchableOpacity>}
    </View>
  );
}

export function NetworkError({ onRetry }: { onRetry: () => void }) {
  return (
    <View style={es.center}>
      <Text style={{ fontSize: 48 }}>📡</Text>
      <Text style={[typography.title, { color: '#9CA3AF', marginTop: 12 }]}>No connection</Text>
      <Text style={[typography.bodySmall, { color: '#6B7280', marginTop: 4 }]}>Check your internet and try again.</Text>
      <TouchableOpacity onPress={onRetry} style={es.btn}><Text style={{ color: '#FFF', fontWeight: '600' }}>Retry</Text></TouchableOpacity>
    </View>
  );
}

const es = StyleSheet.create({
  center: { alignItems: 'center', padding: spacing.xxxl },
  btn: { marginTop: 20, paddingVertical: 12, paddingHorizontal: 24, backgroundColor: '#3B82F6', borderRadius: 8 },
});
