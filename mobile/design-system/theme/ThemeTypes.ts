import { brand, success, warning, danger, info, neutral } from '../tokens';
import { surface, text } from '../tokens/semanticColors';
import { typography, spacing, radius, elevation, opacity, durations, easings, zIndex, breakpoints } from '../tokens';

export type ThemeMode = 'light' | 'dark' | 'amoled' | 'system';

export interface ThemeContextValue {
  theme: Theme;
  setMode: (m: ThemeMode) => void;
  mode: ThemeMode;
}

export interface Theme {
  mode: ThemeMode;
  palette: {
    brand: typeof brand; success: typeof success; warning: typeof warning;
    danger: typeof danger; info: typeof info; neutral: typeof neutral;
    primary: typeof brand; surface: (typeof surface)['light' | 'dark' | 'amoled']; text: (typeof text)['light' | 'dark' | 'amoled'];
    background: string; isDark: boolean;
  };
  tokens: {
    typography: typeof typography; spacing: typeof spacing; radius: typeof radius;
    elevation: typeof elevation; opacity: typeof opacity;
    durations: typeof durations; easings: typeof easings;
    zIndex: typeof zIndex; breakpoints: typeof breakpoints;
  };
}