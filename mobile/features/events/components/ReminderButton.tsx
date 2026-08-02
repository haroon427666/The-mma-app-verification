/** ReminderButton — create/cancel reminder with presets */
import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { typography, radius } from '@/theme';

export function ReminderButton({ hasReminder, onCreate, onCancel, palette }: {
  hasReminder: boolean; onCreate: () => void; onCancel: () => void; palette: any;
}) {
  if (hasReminder) {
    return (
      <TouchableOpacity onPress={onCancel} style={[s.btn, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} accessibilityLabel="Cancel reminder">
        <Text style={[typography.bodySmall, { color: palette.text.primary }]}>🔔 Reminded</Text>
      </TouchableOpacity>
    );
  }
  return (
    <TouchableOpacity onPress={onCreate} style={[s.btn, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]} accessibilityLabel="Set reminder">
      <Text style={[typography.bodySmall, { color: palette.text.primary }]}>🔔 Remind</Text>
    </TouchableOpacity>
  );
}
const s = StyleSheet.create({ btn: { flex: 1, paddingVertical: 12, borderRadius: radius.md, borderWidth: 1, alignItems: 'center' } });
