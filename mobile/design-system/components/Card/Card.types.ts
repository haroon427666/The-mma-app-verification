import type { ReactNode } from 'react';
export type CardVariant = 'elevated' | 'glass' | 'outlined';
export interface CardProps { children: ReactNode; variant?: CardVariant; padding?: number; onPress?: () => void; style?: any; accessibilityLabel?: string; }