import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export function SplashContainer() {
  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.content}>
        <Text style={styles.title}>MMA</Text>
        <Text style={styles.subtitle}>Intelligence</Text>
        <ActivityIndicator size="large" color="#3B82F6" style={styles.spinner} />
      </View>
    </SafeAreaView>
  );
}

export function MaintenanceScreen() {
  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.content}>
        <Text style={styles.icon}>🔧</Text>
        <Text style={styles.title}>Under Maintenance</Text>
        <Text style={styles.subtitle}>We'll be back shortly</Text>
      </View>
    </SafeAreaView>
  );
}

export function OfflineBanner() {
  return (
    <View style={styles.banner}>
      <Text style={styles.bannerText}>You're offline. Changes will sync when connected.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#0A0A0A', justifyContent: 'center', alignItems: 'center' },
  content: { alignItems: 'center' },
  title: { color: '#FFFFFF', fontSize: 42, fontWeight: '800', letterSpacing: 2 },
  subtitle: { color: '#9CA3AF', fontSize: 16, marginTop: 4, letterSpacing: 4, textTransform: 'uppercase' },
  spinner: { marginTop: 48 },
  icon: { fontSize: 48, marginBottom: 16 },
  banner: { backgroundColor: '#F59E0B', padding: 8, alignItems: 'center' },
  bannerText: { color: '#000', fontSize: 12, fontWeight: '600' },
});
