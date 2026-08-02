/** Select, SearchInput — form components */
import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, TextInput, FlatList, Modal, Pressable, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { radius, spacing } from '../../tokens';

// ── Select ──
export interface SelectProps { value: string; options: { label: string; value: string }[]; onChange: (v: string) => void; placeholder?: string; label?: string; }
export const Select = ({ value, options, onChange, placeholder = 'Select...', label }: SelectProps) => {
  const { palette } = useTheme();
  const [open, setOpen] = useState(false);
  const selectedLabel = options.find(o => o.value === value)?.label || placeholder;
  return (
    <View style={{ marginBottom: spacing.md }}>
      {label && <Text style={[s.label, { color: palette.text.secondary }]}>{label}</Text>}
      <TouchableOpacity onPress={() => setOpen(true)} style={[s.select, { backgroundColor: palette.surface.elevated, borderColor: palette.surface.border }]}>
        <Text style={[{ color: value ? palette.text.primary : palette.text.tertiary, flex: 1 }]}>{selectedLabel}</Text><Text style={{ color: palette.text.tertiary }}>▼</Text>
      </TouchableOpacity>
      <Modal visible={open} transparent animationType="fade" onRequestClose={() => setOpen(false)}>
        <Pressable style={s.overlay} onPress={() => setOpen(false)}>
          <View style={[s.dropdown, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            {options.map(o => (
              <TouchableOpacity key={o.value} onPress={() => { onChange(o.value); setOpen(false); }} style={[s.option, o.value === value && { backgroundColor: palette.surface.elevated }]}>
                <Text style={[{ color: palette.text.primary }, o.value === value && { color: palette.primary[400], fontWeight: '700' }]}>{o.label}{o.value === value ? ' ✓' : ''}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </Pressable>
      </Modal>
    </View>
  );
};

// ── SearchInput ──
export interface SearchInputProps { value: string; onChangeText: (t: string) => void; placeholder?: string; onFocus?: () => void; onBlur?: () => void; }
export const SearchInput = ({ value, onChangeText, placeholder = 'Search...', onFocus, onBlur }: SearchInputProps) => {
  const { palette } = useTheme();
  return (
    <View style={[si.wrap, { backgroundColor: palette.surface.elevated, borderColor: palette.surface.border }]}>
      <Text style={si.icon}>🔍</Text>
      <TextInput style={[si.input, { color: palette.text.primary }]} placeholder={placeholder} placeholderTextColor={palette.text.tertiary} value={value} onChangeText={onChangeText} onFocus={onFocus} onBlur={onBlur} />
      {value ? <TouchableOpacity onPress={() => onChangeText('')}><Text style={{ color: palette.text.tertiary, fontSize: 18 }}>✕</Text></TouchableOpacity> : null}
    </View>
  );
};

// ── Tooltip ──
export const Tooltip = ({ children, label }: { children: React.ReactNode; label: string }) => {
  const [show, setShow] = useState(false);
  return (
    <View>
      <TouchableOpacity onPress={() => setShow(!show)}>{children}</TouchableOpacity>
      {show && <View style={[t.wrap, { backgroundColor: '#1F2937' }]}><Text style={t.text}>{label}</Text></View>}
    </View>
  );
};

// ── Accordion ──
export const Accordion = ({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) => {
  const { palette } = useTheme();
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={[a.wrap, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <TouchableOpacity onPress={() => setOpen(!open)} style={a.header}>
        <Text style={[a.title, { color: palette.text.primary }]}>{title}</Text><Text style={{ color: palette.text.tertiary }}>{open ? '▲' : '▼'}</Text>
      </TouchableOpacity>
      {open && <View style={a.body}>{children}</View>}
    </View>
  );
};

// ── Breadcrumb ──
export const Breadcrumb = ({ items, onPress }: { items: string[]; onPress?: (part: string, index: number) => void }) => {
  const { palette } = useTheme();
  return (
    <View style={bc.wrap}>
      {items.map((item, i) => (
        <View key={i} style={bc.item}>
          <TouchableOpacity onPress={() => onPress?.(item, i)}><Text style={[bc.link, { color: i < items.length - 1 ? palette.primary[400] : palette.text.primary }]}>{item}</Text></TouchableOpacity>
          {i < items.length - 1 && <Text style={[bc.sep, { color: palette.text.tertiary }]}> / </Text>}
        </View>
      ))}
    </View>
  );
};

// ── Calendar (month view) ──
export const Calendar = ({ date, onSelect }: { date?: Date; onSelect?: (d: Date) => void }) => {
  const [current, setCurrent] = useState(date || new Date());
  const { palette } = useTheme();
  const year = current.getFullYear(); const month = current.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = new Date().getDate();
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const weekDays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
  return (
    <View style={[cal.wrap, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={cal.header}>
        <TouchableOpacity onPress={() => setCurrent(new Date(year, month - 1))}><Text style={{ color: palette.primary[400], fontSize: 18 }}>‹</Text></TouchableOpacity>
        <Text style={[cal.month, { color: palette.text.primary }]}>{current.toLocaleString('default', { month: 'long', year: 'numeric' })}</Text>
        <TouchableOpacity onPress={() => setCurrent(new Date(year, month + 1))}><Text style={{ color: palette.primary[400], fontSize: 18 }}>›</Text></TouchableOpacity>
      </View>
      <View style={cal.weekRow}>{weekDays.map(d => <Text key={d} style={[cal.wd, { color: palette.text.tertiary }]}>{d}</Text>)}</View>
      <View style={cal.grid}>
        {Array.from({ length: firstDay }).map((_, i) => <View key={`e${i}`} style={cal.cell} />)}
        {days.map(d => (
          <TouchableOpacity key={d} onPress={() => onSelect?.(new Date(year, month, d))} style={[cal.cell, d === today && { backgroundColor: palette.primary[500] + '30' }]}>
            <Text style={[cal.day, { color: d === today ? palette.primary[400] : palette.text.primary, fontWeight: d === today ? '700' : '400' }]}>{d}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

// ── Snackbar ──
export const Snackbar = ({ visible, message, action, onAction }: { visible: boolean; message: string; action?: string; onAction?: () => void }) => {
  if (!visible) return null;
  return (
    <View style={sn.wrap}>
      <Text style={sn.text}>{message}</Text>
      {action && <TouchableOpacity onPress={onAction}><Text style={sn.action}>{action}</Text></TouchableOpacity>}
    </View>
  );
};

// ── Carousel ──
export const Carousel = ({ children }: { children: React.ReactNode[] }) => {
  const [idx, setIdx] = useState(0);
  const { palette } = useTheme();
  return (
    <View>
      <View style={car.slide}>{children[idx]}</View>
      <View style={car.dots}>{children.map((_, i) => <TouchableOpacity key={i} onPress={() => setIdx(i)}><View style={[car.dot, { backgroundColor: i === idx ? palette.primary[400] : palette.surface.elevated }]} /></TouchableOpacity>)}</View>
    </View>
  );
};

// ── Styles ──
const s = StyleSheet.create({ label: { fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }, select: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, height: 48, borderRadius: radius.md, borderWidth: 1.5 }, overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 40 }, dropdown: { borderRadius: radius.lg, borderWidth: 1, overflow: 'hidden' }, option: { padding: spacing.md } });
const si = StyleSheet.create({ wrap: { flexDirection: 'row', alignItems: 'center', borderRadius: radius.md, paddingHorizontal: 14, borderWidth: 1.5, height: 48 }, icon: { marginRight: 8, fontSize: 16 }, input: { flex: 1, fontSize: 16 } });
const t = StyleSheet.create({ wrap: { position: 'absolute', bottom: '110%', left: 0, right: 0, padding: 8, borderRadius: 8, zIndex: 9999 }, text: { color: '#FFF', fontSize: 12 } });
const a = StyleSheet.create({ wrap: { borderRadius: radius.md, borderWidth: 0.5, overflow: 'hidden' }, header: { flexDirection: 'row', justifyContent: 'space-between', padding: spacing.md }, body: { padding: spacing.md }, title: { fontSize: 16, fontWeight: '600' } });
const bc = StyleSheet.create({ wrap: { flexDirection: 'row', flexWrap: 'wrap', paddingVertical: 8 }, item: { flexDirection: 'row', alignItems: 'center' }, link: { fontSize: 14 }, sep: { fontSize: 14, marginHorizontal: 4 } });
const cal = StyleSheet.create({ wrap: { borderRadius: radius.lg, borderWidth: 0.5, padding: spacing.md }, header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md }, month: { fontSize: 16, fontWeight: '700' }, weekRow: { flexDirection: 'row', marginBottom: spacing.sm }, wd: { flex: 1, textAlign: 'center', fontSize: 12, fontWeight: '600' }, grid: { flexDirection: 'row', flexWrap: 'wrap' }, cell: { width: '14.28%', aspectRatio: 1, alignItems: 'center', justifyContent: 'center' }, day: { fontSize: 14 } });
const sn = StyleSheet.create({ wrap: { position: 'absolute', bottom: 40, left: 16, right: 16, backgroundColor: '#1F2937', padding: spacing.md, borderRadius: radius.md, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', zIndex: 9999, elevation: 10 }, text: { color: '#FFF', fontSize: 14, flex: 1 }, action: { color: '#3B82F6', fontWeight: '700', marginLeft: 12 } });
const car = StyleSheet.create({ slide: { borderRadius: radius.lg, overflow: 'hidden' }, dots: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginTop: 12 }, dot: { width: 8, height: 8, borderRadius: 4 } });