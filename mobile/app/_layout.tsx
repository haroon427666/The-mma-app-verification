import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StyleSheet, View } from 'react-native';
import { Slot } from 'expo-router';

import { QueryProvider } from '@/providers/QueryProvider';
import { AuthProvider } from '@/providers/AuthProvider';
import { NotificationProvider } from '@/providers/NotificationProvider';
import { useTheme } from '@/hooks/useTheme';
import { useNetwork } from '@/hooks/useNetwork';
import { useUIStore } from '@/stores/ui';
import { SplashContainer } from '@/components/shell/SplashScreen';
import { MaintenanceScreen } from '@/components/shell/MaintenanceScreen';
import { OfflineBanner } from '@/components/shell/OfflineBanner';

function AppContent({ children }: { children: React.ReactNode }) {
  const { palette } = useTheme();
  const { isOffline } = useNetwork();
  const isSplashVisible = useUIStore((s) => s.isSplashVisible);
  const isMaintenanceMode = useUIStore((s) => s.isMaintenanceMode);

  if (isSplashVisible) return <SplashContainer />;
  if (isMaintenanceMode) return <MaintenanceScreen />;

  return (
    <View style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <StatusBar style={palette.isDark ? 'light' : 'dark'} />
      {isOffline && <OfflineBanner />}
      {children}
    </View>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={styles.gesture}>
      <SafeAreaProvider>
        <QueryProvider>
          <AuthProvider>
            <NotificationProvider>
              <AppContent>
                <Slot />
              </AppContent>
            </NotificationProvider>
          </AuthProvider>
        </QueryProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  gesture: { flex: 1 },
  root: { flex: 1 },
});
