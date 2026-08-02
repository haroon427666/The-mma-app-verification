/** Button types */
import type { ReactNode } from 'react';
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg';
export interface ButtonProps {
  variant?: ButtonVariant; size?: ButtonSize; label: string; onPress?: () => void;
  loading?: boolean; disabled?: boolean; icon?: ReactNode; iconRight?: ReactNode;
  fullWidth?: boolean; style?: any; accessibilityLabel?: string;
}