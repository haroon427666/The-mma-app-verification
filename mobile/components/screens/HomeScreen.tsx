/** Home Screen placeholder — populated in Part 2 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography } from '@/theme';

export function HomeScreen() {
  const { palette } = useTheme();
  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <Text style={[typography.title, { color: palette.text.primary }]}>Home</Text>
      <Text style={{ color: palette.text.secondary, marginTop: 8 }}>Live events, upcoming fights, AI insights — coming in Part 2</Text>
    </SafeAreaView>
  );
}

export function EventsScreen() {
  const { palette } = useTheme();
  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <Text style={[typography.title, { color: palette.text.primary }]}>Events</Text>
    </SafeAreaView>
  );
}

export function RankingsScreen() {
  const { palette } = useTheme();
  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <Text style={[typography.title, { color: palette.text.primary }]}>Rankings</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 20 },
});
