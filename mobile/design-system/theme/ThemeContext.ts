import { createContext } from 'react';
import type { Theme, ThemeMode } from './ThemeTypes';

export interface ThemeContextValue { theme: Theme; setMode: (m: ThemeMode) => void; mode: ThemeMode; }

export const ThemeContext = createContext<ThemeContextValue | null>(null);