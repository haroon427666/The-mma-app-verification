/** AuthProvider — session restore, Biometric unlock */

import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useAuthStore } from '@/stores/auth';
import { authService } from '@/services/auth';
import { useUIStore } from '@/stores/ui';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isReady, setIsReady] = useState(false);
  const [needsBiometric, setNeedsBiometric] = useState(false);
  const store = useAuthStore();

  useEffect(() => {
    (async () => {
      try {
        const restored = await authService.restoreSession();
        if (restored && store.isBiometricEnabled) {
          const ok = await authService.authenticateWithBiometric();
          if (!ok) {
            store.logout();
            useUIStore.getState().hideSplash();
            setIsReady(true);
            return;
          }
        }
      } catch {
        store.setStatus('unauthenticated');
      }
      useUIStore.getState().hideSplash();
      setIsReady(true);
    })();
  }, []);

  if (!isReady) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.text}>Loading...</Text>
      </View>
    );
  }

  return <>{children}</>;
}

const styles = StyleSheet.create({
  container: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#0A0A0A',
  },
  text: { color: '#9CA3AF', marginTop: 16, fontSize: 14 },
});
