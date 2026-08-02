import React, { forwardRef, useMemo } from 'react';
import { Text, Pressable, ActivityIndicator, View } from 'react-native';
import { useTheme } from '../../theme';
import { radius } from '../../tokens';
import { btnStyles } from './Button.styles';
import { resolveButtonColors, buttonSizes } from './Button.utils';
import type { ButtonProps } from './Button.types';

export const Button = forwardRef<any, ButtonProps>(({ variant = 'primary', size = 'md', label, onPress, loading, disabled, icon, iconRight, fullWidth, style, accessibilityLabel }, ref) => {
  const { palette } = useTheme();
  const c = useMemo(() => resolveButtonColors(variant, palette.isDark), [variant, palette.isDark]);
  const sz = buttonSizes[size];

  return (
    <Pressable ref={ref} onPress={onPress} disabled={disabled || loading}
      style={({ pressed }) => [btnStyles.base, { height: sz.h, paddingHorizontal: sz.px, backgroundColor: c.bg, borderColor: c.border, borderWidth: variant === 'outline' ? 1.5 : 0, opacity: (disabled || loading) ? 0.5 : pressed ? 0.85 : 1, borderRadius: radius.md }, fullWidth && btnStyles.full, style]}
      accessibilityRole="button" accessibilityLabel={accessibilityLabel || label} accessibilityState={{ disabled: disabled || loading }}>
      {loading ? <ActivityIndicator color={c.text} style={{ marginRight: 8 }} /> : icon ? <View style={{ marginRight: 8 }}>{icon}</View> : null}
      <Text style={[btnStyles.label, { color: c.text, fontSize: sz.fs }]}>{label}</Text>
      {iconRight && <View style={{ marginLeft: 8 }}>{iconRight}</View>}
    </Pressable>
  );
});
Button.displayName = 'Button';