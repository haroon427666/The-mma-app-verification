/** Root navigator — switches between Auth and Main based on auth state */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuthStore } from '@/stores/auth';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { ModalNavigator } from './ModalNavigator';

const Stack = createNativeStackNavigator();

export function RootNavigator() {
  const isAuthenticated = useAuthStore((s) => s.status === 'authenticated');

  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'fade' }}>
      {isAuthenticated ? (
        <>
          <Stack.Screen name="main" component={MainNavigator} />
          <Stack.Screen
            name="modal"
            component={ModalNavigator}
            options={{ presentation: 'modal', animation: 'slide_from_bottom' }}
          />
        </>
      ) : (
        <Stack.Screen name="auth" component={AuthNavigator} />
      )}
    </Stack.Navigator>
  );
}
