/** Extended tokens — gradients, glass, blur, grid, brand themes */
import { brand, neutral } from '../colors';

// Glass effect presets
export const glass = {
  light: { backgroundColor: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(10px)' },
  dark: { backgroundColor: 'rgba(26,26,46,0.8)', backdropFilter: 'blur(10px)' },
};

// Blur presets
export const blurAmounts = { subtle: 4, medium: 10, heavy: 20, extreme: 40 } as const;

// Gradients
export const gradients = {
  brand: ['#3B82F6', '#8B5CF6'] as const,
  success: ['#10B981', '#34D399'] as const,
  danger: ['#EF4444', '#F87171'] as const,
  warm: ['#F59E0B', '#F97316'] as const,
  cool: ['#3B82F6', '#06B6D4'] as const,
  dark: ['#1A1A2E', '#0A0A0A'] as const,
};

// Grid system
export const grid = { columns: 12, gutter: 16, margin: 24, maxWidth: 1200 } as const;

// Brand themes
export const brandThemes = {
  mma: { primary: brand[500], accent: '#F59E0B', surface: '#0A0A0A' },
  ufc: { primary: '#D32F2F', accent: '#C8AA6E', surface: '#1A1A1A' },
};

// Accessibility colors
export const a11yColors = {
  focus: '#3B82F6', focusRing: 'rgba(59,130,246,0.4)',
  highContrastBorder: '#FFFFFF',
  errorBorder: '#EF4444',
} as const;