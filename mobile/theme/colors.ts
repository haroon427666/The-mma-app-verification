/** Design tokens — the single source of truth for all visual values. */

type ColorScale = {
  50: string; 100: string; 200: string; 300: string;
  400: string; 500: string; 600: string; 700: string;
  800: string; 900: string; 950: string;
};

export const colors = {
  primary: {
    50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE',
    300: '#93C5FD', 400: '#60A5FA', 500: '#3B82F6',
    600: '#2563EB', 700: '#1D4ED8', 800: '#1E40AF',
    900: '#1E3A8A', 950: '#172554',
  } as ColorScale,

  accent: {
    light: '#F59E0B',  // Amber
    dark: '#FBBF24',
  },

  surface: {
    light: {
      bg: '#FFFFFF',
      card: '#F9FAFB',
      elevated: '#FFFFFF',
      overlay: 'rgba(0,0,0,0.5)',
      border: '#E5E7EB',
      divider: '#F3F4F6',
    },
    dark: {
      bg: '#0A0A0A',
      card: '#1A1A2E',
      elevated: '#222240',
      overlay: 'rgba(0,0,0,0.7)',
      border: '#2A2A3E',
      divider: '#1E1E32',
    },
    amoled: {
      bg: '#000000',
      card: '#0D0D0D',
      elevated: '#161616',
      overlay: 'rgba(0,0,0,0.85)',
      border: '#1A1A1A',
      divider: '#111111',
    },
  },

  text: {
    light: { primary: '#111827', secondary: '#6B7280', tertiary: '#9CA3AF', inverse: '#FFFFFF' },
    dark:  { primary: '#F9FAFB', secondary: '#9CA3AF', tertiary: '#6B7280', inverse: '#0A0A0A' },
    amoled:{ primary: '#FAFAFA', secondary: '#A0A0B0', tertiary: '#666680', inverse: '#000000' },
  },

  status: {
    success: '#10B981', warning: '#F59E0B',
    error: '#EF4444', info: '#3B82F6',
    ko: '#EF4444', submission: '#8B5CF6',
    decision: '#3B82F6', draw: '#6B7280',
  },

  championship: '#F59E0B',
  ufc: '#D32F2F',
} as const;
