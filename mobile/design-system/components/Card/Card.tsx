import React from 'react';
import { TouchableOpacity, View } from 'react-native';
import { useTheme } from '../../theme';
import { radius } from '../../tokens';
import type { CardProps } from './Card.types';

export const Card = ({ children, variant = 'elevated', padding = 16, onPress, style, accessibilityLabel }: CardProps) => {
  const { palette } = useTheme();
  const shadow = variant === 'elevated' ? { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 3 } : {};
  const Wrapper = onPress ? TouchableOpacity : View;
  return (
    <Wrapper onPress={onPress} activeOpacity={0.7} accessibilityRole={onPress ? 'button' : 'none'} accessibilityLabel={accessibilityLabel}
      style={[{ padding, backgroundColor: palette.surface.card, borderRadius: radius.lg, borderWidth: variant === 'outlined' ? 1 : 0, borderColor: palette.surface.border, ...shadow }, style]}>
      {children}
    </Wrapper>
  );
};