import React from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { radius } from '../../tokens';
import type { TextFieldProps } from './TextField.types';

export const TextField = ({ label, error, leftIcon, rightIcon, ...props }: TextFieldProps) => {
  const { palette } = useTheme();
  return (
    <View style={{ marginBottom: 16 }}>
      {label && <Text style={s.label}>{label}</Text>}
      <View style={[s.wrap, { backgroundColor: palette.surface.elevated, borderColor: error ? palette.danger[400] : palette.surface.border }]}>
        {leftIcon && <View style={{ marginRight: 10 }}>{leftIcon}</View>}
        <TextInput style={[s.field, { color: palette.text.primary }]} placeholderTextColor={palette.text.tertiary} {...props} />
        {rightIcon || (props.value ? <TouchableOpacity onPress={() => props.onChangeText('')}><Text style={{ color: palette.text.tertiary, fontSize: 18 }}>✕</Text></TouchableOpacity> : null)}
      </View>
      {error && <Text style={[s.error, { color: palette.danger[400] }]}>{error}</Text>}
    </View>
  );
};
const s = StyleSheet.create({ label: { fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6, color: '#9CA3AF' }, wrap: { flexDirection: 'row', alignItems: 'center', borderWidth: 1.5, borderRadius: radius.md, paddingHorizontal: 14, height: 48 }, field: { flex: 1, fontSize: 16, paddingVertical: 0 }, error: { fontSize: 12, marginTop: 4 } });