/** IconButton — Icon-only button */
import React from 'react';
import { TouchableOpacity, Text, View } from 'react-native';
import { useTheme } from '../../theme';
export const IconButton = ({ icon, onPress, size = 40, color }: { icon: string; onPress?: () => void; size?: number; color?: string }) => {
  const { palette } = useTheme();
  return <TouchableOpacity onPress={onPress} style={{ width: size, height: size, borderRadius: size / 2, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.surface.elevated }} accessibilityRole="button"><Text style={{ fontSize: size / 2, color: color || palette.text.primary }}>{icon}</Text></TouchableOpacity>;
};