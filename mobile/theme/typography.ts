/** Typography scale */

import { Platform } from 'react-native';

const fontFamily = Platform.select({
  ios: 'System',
  android: 'System',
  default: 'System',
});

const monoFamily = Platform.select({
  ios: 'Menlo',
  android: 'monospace',
  default: 'monospace',
});

export const typography = {
  display: {
    fontSize: 36, lineHeight: 44, fontWeight: '800' as const,
    fontFamily, letterSpacing: -0.5,
  },
  headline: {
    fontSize: 28, lineHeight: 36, fontWeight: '700' as const,
    fontFamily, letterSpacing: -0.3,
  },
  title: {
    fontSize: 22, lineHeight: 30, fontWeight: '600' as const,
    fontFamily, letterSpacing: -0.2,
  },
  subtitle: {
    fontSize: 18, lineHeight: 26, fontWeight: '600' as const,
    fontFamily,
  },
  body: {
    fontSize: 16, lineHeight: 24, fontWeight: '400' as const,
    fontFamily,
  },
  bodySmall: {
    fontSize: 14, lineHeight: 20, fontWeight: '400' as const,
    fontFamily,
  },
  caption: {
    fontSize: 12, lineHeight: 16, fontWeight: '400' as const,
    fontFamily,
  },
  button: {
    fontSize: 16, lineHeight: 24, fontWeight: '600' as const,
    fontFamily, letterSpacing: 0.3,
  },
  mono: {
    fontSize: 14, lineHeight: 20, fontWeight: '400' as const,
    fontFamily: monoFamily,
  },
  overline: {
    fontSize: 10, lineHeight: 14, fontWeight: '700' as const,
    fontFamily, letterSpacing: 1.5, textTransform: 'uppercase' as const,
  },
} as const;
