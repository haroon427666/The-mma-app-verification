/** Provider Composer — nests all providers in correct order */
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { ThemeProvider } from '../../design-system/theme';
import { ErrorBoundary } from './ErrorBoundary';

interface ComposerProps { children: React.ReactNode; providers?: React.ComponentType<{ children: React.ReactNode }>[]; }

export function ProviderComposer({ children, providers = [] }: ComposerProps) {
  const allProviders = [
    ErrorBoundary as any,
    GestureHandlerRootView,
    SafeAreaProvider,
    ThemeProvider,
    ...providers,
  ];

  return allProviders.reduceRight(
    (acc, Provider) => React.createElement(Provider, null, acc),
    children,
  );
}
