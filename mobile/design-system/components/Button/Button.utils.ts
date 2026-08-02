import type { ButtonVariant } from './Button.types';
import { brand, success, danger } from '../../tokens/colors';
import { surface as s, text as t } from '../../tokens/semanticColors';

export function resolveButtonColors(variant: ButtonVariant, isDark: boolean) {
  const mode = isDark ? 'dark' : 'light';
  const map: Record<ButtonVariant, { bg: string; text: string; border: string }> = {
    primary: { bg: brand[500], text: '#FFFFFF', border: 'transparent' },
    secondary: { bg: s[mode].elevated, text: t[mode].primary, border: s[mode].border },
    ghost: { bg: 'transparent', text: brand[400], border: 'transparent' },
    outline: { bg: 'transparent', text: brand[400], border: brand[400] },
    danger: { bg: danger[500], text: '#FFFFFF', border: 'transparent' },
    success: { bg: success[500], text: '#FFFFFF', border: 'transparent' },
  };
  return map[variant];
}

export const buttonSizes = { sm: { h: 36, px: 14, fs: 14 }, md: { h: 48, px: 20, fs: 16 }, lg: { h: 56, px: 24, fs: 18 } };