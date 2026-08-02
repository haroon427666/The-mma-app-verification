/** AppBootstrap — main entry point for application initialization */
import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { ProviderComposer } from './ProviderComposer';
import { AppInitializer } from './AppInitializer';
import { BootstrapContext } from './BootstrapContext';
import { useBootstrapState } from './BootstrapState';

export function AppBootstrap({ children }: { children: React.ReactNode }) {
  const { stage, isReady, progress, error } = useBootstrapState();
  const [initializer] = useState(() => new AppInitializer());

  useEffect(() => { initializer.initialize(); }, []);

  if (!isReady && stage !== 'failed') {
    return (
      <View style={s.splash}>
        <Text style={s.logo}>🥊</Text>
        <Text style={s.appName}>MMA Intelligence</Text>
        <View style={[s.progressBarBg]}>
          <View style={[s.progressBar, { width: `${progress}%` }]} />
        </View>
      </View>
    );
  }

  return (
    <BootstrapContext.Provider value={{ isReady, stage, progress }}>
      <ProviderComposer>{children}</ProviderComposer>
    </BootstrapContext.Provider>
  );
}

const s = StyleSheet.create({
  splash: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0A0A0A' },
  logo: { fontSize: 64 }, appName: { color: '#FFF', fontSize: 24, fontWeight: '800', marginTop: 16 },
  progressBarBg: { width: 200, height: 4, backgroundColor: '#1A1A2E', borderRadius: 2, marginTop: 32, overflow: 'hidden' },
  progressBar: { height: 4, backgroundColor: '#3B82F6', borderRadius: 2 },
});
