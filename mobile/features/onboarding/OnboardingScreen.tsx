/** Onboarding screen — shown once for new users */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius, motion } from '@/theme';

export function OnboardingScreen({ navigation }: any) {
  const { palette } = useTheme();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <View style={s.content}>
        <Text style={{ fontSize: 64, marginBottom: 20 }}>🥊</Text>
        <Text style={[typography.display, { color: palette.text.primary, textAlign: 'center' }]}>Welcome to{'\n'}MMA Intelligence</Text>
        <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 16 }]}>AI-powered predictions, personalized recommendations, and deep analytics for every fight.</Text>
        <TouchableOpacity onPress={() => navigation.replace('login')} style={[s.button, { backgroundColor: palette.primary[500] }]}>
          <Text style={[typography.button, { color: '#FFF' }]}>Get Started</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
const s = StyleSheet.create({
  root: { flex: 1 },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: spacing.xxxl },
  button: { marginTop: spacing.xxxl, paddingVertical: 16, paddingHorizontal: 48, borderRadius: radius.lg },
});
