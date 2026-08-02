/** useTheme — resolves theme with system preference */

import { useColorScheme } from 'react-native';
import { useMemo } from 'react';
import { useUIStore } from '@/stores/ui';
import { colors } from '@/theme/colors';

export function useTheme() {
  const systemScheme = useColorScheme();
  const theme = useUIStore((s) => s.theme);

  const resolved = useMemo(() => {
    if (theme === 'system') return systemScheme === 'dark' ? 'dark' : 'light';
    if (theme === 'amoled') return 'amoled';
    return theme;
  }, [theme, systemScheme]);

  const palette = useMemo(() => ({
    ...colors,
    surface: colors.surface[resolved],
    text: colors.text[resolved],
    isDark: resolved !== 'light',
  }), [resolved]);

  return { theme: resolved, palette, isDark: palette.isDark };
}
