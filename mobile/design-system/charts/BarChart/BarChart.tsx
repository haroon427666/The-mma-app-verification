import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { chartColors } from '../../tokens';

export const BarChart = ({ data, labels }: { data: number[]; labels?: string[] }) => { const { palette } = useTheme(); const max = Math.max(...data, 1); return (<View style={s.wrap}>{data.map((v, i) => (<View key={i} style={s.barRow}><Text style={[s.label, { color: palette.text.secondary }]}>{labels?.[i] || ''}</Text><View style={[s.barBg, { backgroundColor: palette.surface.elevated }]}><View style={[s.bar, { width: `${(v / max) * 100}%`, backgroundColor: chartColors.primary }]} /></View><Text style={[s.val, { color: palette.text.primary }]}>{v}</Text></View>))}</View>); };
export const LineChart = () => null;
export const RadarChart = () => null;
export const PieChart = () => null;
const s = StyleSheet.create({ wrap: { marginVertical: 8 }, barRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 }, label: { width: 60, fontSize: 12 }, barBg: { flex: 1, height: 10, borderRadius: 5, overflow: 'hidden', marginHorizontal: 8 }, bar: { height: 10, borderRadius: 5 }, val: { width: 36, fontSize: 12, textAlign: 'right', fontWeight: '600' } });