/** Switch, SegmentedControl, Checkbox, Radio — Toggle components */
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Pressable, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { radius, spacing } from '../../tokens';

// ── Switch ──
export interface SwitchProps { value: boolean; onValueChange: (v: boolean) => void; disabled?: boolean; label?: string; }
export const Switch = ({ value, onValueChange, disabled, label }: SwitchProps) => {
  const { palette } = useTheme();
  return (
    <Pressable onPress={() => !disabled && onValueChange(!value)} style={sw.row} accessibilityRole="switch" accessibilityState={{ checked: value, disabled }}>
      {label && <Text style={[sw.label, { color: palette.text.primary }]}>{label}</Text>}
      <View style={[sw.track, { backgroundColor: value ? palette.primary[500] : palette.surface.elevated, opacity: disabled ? 0.5 : 1 }]}>
        <View style={[sw.thumb, value && sw.thumbOn]} />
      </View>
    </Pressable>
  );
};

// ── Checkbox ──
export interface CheckboxProps { checked: boolean; onToggle: () => void; label?: string; disabled?: boolean; }
export const Checkbox = ({ checked, onToggle, label, disabled }: CheckboxProps) => {
  const { palette } = useTheme();
  return (
    <TouchableOpacity onPress={onToggle} disabled={disabled} style={cx.row} accessibilityRole="checkbox" accessibilityState={{ checked, disabled }}>
      <View style={[cx.box, { borderColor: checked ? palette.primary[500] : palette.text.tertiary, backgroundColor: checked ? palette.primary[500] : 'transparent', opacity: disabled ? 0.5 : 1 }]}>
        {checked && <Text style={cx.check}>✓</Text>}
      </View>
      {label && <Text style={[cx.label, { color: palette.text.primary }]}>{label}</Text>}
    </TouchableOpacity>
  );
};

// ── Radio ──
export interface RadioProps<T = string> { value: T; selected: T; onSelect: (v: T) => void; label?: string; }
export function Radio<T extends string>({ value, selected, onSelect, label }: RadioProps<T>) {
  const { palette } = useTheme();
  const isSelected = value === selected;
  return (
    <TouchableOpacity onPress={() => onSelect(value)} style={cx.row} accessibilityRole="radio" accessibilityState={{ selected: isSelected }}>
      <View style={[rd.outer, { borderColor: isSelected ? palette.primary[500] : palette.text.tertiary }]}>
        {isSelected && <View style={[rd.inner, { backgroundColor: palette.primary[500] }]} />}
      </View>
      {label && <Text style={[cx.label, { color: palette.text.primary }]}>{label}</Text>}
    </TouchableOpacity>
  );
}

// ── SegmentedControl ──
export interface SegmentedControlProps<T extends string = string> { options: { label: string; value: T }[]; value: T; onChange: (v: T) => void; }
export function SegmentedControl<T extends string>({ options, value, onChange }: SegmentedControlProps<T>) {
  const { palette } = useTheme();
  return (
    <View style={[sg.wrap, { backgroundColor: palette.surface.elevated, borderColor: palette.surface.border }]}>
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <TouchableOpacity key={opt.value} onPress={() => onChange(opt.value)} style={[sg.option, active && { backgroundColor: palette.primary[500] }]} accessibilityRole="button" accessibilityState={{ selected: active }}>
            <Text style={[sg.text, { color: active ? '#FFF' : palette.text.secondary }]}>{opt.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

// ── Stepper ──
export const Stepper = ({ value, onIncrement, onDecrement, min = 0, max = 99 }: { value: number; onIncrement: () => void; onDecrement: () => void; min?: number; max?: number }) => {
  const { palette } = useTheme();
  return (
    <View style={st.wrap}>
      <TouchableOpacity onPress={onDecrement} disabled={value <= min} style={[st.btn, { backgroundColor: palette.surface.elevated, opacity: value <= min ? 0.4 : 1 }]}><Text style={{ color: palette.text.primary, fontSize: 20 }}>−</Text></TouchableOpacity>
      <Text style={[st.val, { color: palette.text.primary }]}>{value}</Text>
      <TouchableOpacity onPress={onIncrement} disabled={value >= max} style={[st.btn, { backgroundColor: palette.surface.elevated, opacity: value >= max ? 0.4 : 1 }]}><Text style={{ color: palette.text.primary, fontSize: 20 }}>+</Text></TouchableOpacity>
    </View>
  );
};

// ── Styles ──
const sw = StyleSheet.create({ row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.sm }, label: { fontSize: 16, marginRight: 12 }, track: { width: 48, height: 28, borderRadius: 14, justifyContent: 'center', paddingHorizontal: 2 }, thumb: { width: 24, height: 24, borderRadius: 12, backgroundColor: '#FFFFFF' }, thumbOn: { alignSelf: 'flex-end' } });
const cx = StyleSheet.create({ row: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 }, box: { width: 22, height: 22, borderRadius: 4, borderWidth: 2, alignItems: 'center', justifyContent: 'center' }, check: { color: '#FFF', fontSize: 14, fontWeight: '700' }, label: { marginLeft: 10, fontSize: 16 } });
const rd = StyleSheet.create({ outer: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, alignItems: 'center', justifyContent: 'center' }, inner: { width: 12, height: 12, borderRadius: 6 } });
const sg = StyleSheet.create({ wrap: { flexDirection: 'row', borderRadius: radius.md, borderWidth: 1, overflow: 'hidden' }, option: { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: radius.sm }, text: { fontSize: 14, fontWeight: '600' } });
const st = StyleSheet.create({ wrap: { flexDirection: 'row', alignItems: 'center', gap: 12 }, btn: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' }, val: { fontSize: 18, fontWeight: '700', minWidth: 30, textAlign: 'center' } });