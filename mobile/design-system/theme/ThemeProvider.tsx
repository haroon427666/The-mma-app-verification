import React, { useMemo, useState } from 'react';
import { useColorScheme, StatusBar } from 'react-native';
import { ThemeContext } from './ThemeContext';
import { buildTheme } from './ThemeBuilder';
import type { ThemeMode } from './ThemeTypes';

export function ThemeProvider({ children, initialMode = 'dark' }: { children: React.ReactNode; initialMode?: ThemeMode }) {
  const systemScheme = useColorScheme();
  const [mode, setMode] = useState<ThemeMode>(initialMode);
  const systemIsDark = systemScheme === 'dark';
  const theme = useMemo(() => buildTheme(mode, systemIsDark), [mode, systemIsDark]);
  return (
    <ThemeContext.Provider value={{ theme, setMode, mode }}>
      <StatusBar barStyle={theme.palette.isDark ? 'light-content' : 'dark-content'} backgroundColor={theme.palette.background} />
      {children}
    </ThemeContext.Provider>
  );
}