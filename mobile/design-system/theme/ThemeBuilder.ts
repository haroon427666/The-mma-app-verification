import type { Theme, ThemeMode } from './ThemeTypes';
import { brand, success, warning, danger, info, neutral, typography, spacing, radius, elevation, opacity, durations, easings, zIndex, breakpoints } from '../tokens';
import { surface, text } from '../tokens/semanticColors';

function buildPalette(effectiveMode: 'light' | 'dark' | 'amoled') {
  const isDark = effectiveMode !== 'light';
  const surf = effectiveMode === 'amoled' ? surface.amoled : isDark ? surface.dark : surface.light;
  const txt = effectiveMode === 'amoled' ? text.amoled : isDark ? text.dark : text.light;
  return { brand, success, warning, danger, info, neutral, primary: brand, surface: surf, text: txt, background: surf.bg, isDark };
}

export function buildTheme(mode: ThemeMode, systemIsDark: boolean): Theme {
  const effectiveMode = mode === 'system' ? (systemIsDark ? 'dark' : 'light') : mode;
  return { mode, palette: buildPalette(effectiveMode as 'light' | 'dark' | 'amoled'), tokens: { typography, spacing, radius, elevation, opacity, durations, easings, zIndex, breakpoints } };
}

export const darkTheme = buildTheme('dark', true);
export const lightTheme = buildTheme('light', false);
export const amoledTheme = buildTheme('amoled', true);