import { useContext } from 'react';
import { ThemeContext } from './ThemeContext';
import type { ThemeContextValue } from './ThemeContext';

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return { theme: ctx.theme, setMode: ctx.setMode, mode: ctx.mode, palette: ctx.theme.palette, tokens: ctx.theme.tokens } as const;
}