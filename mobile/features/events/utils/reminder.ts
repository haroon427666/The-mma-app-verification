/** Reminder utilities — time calculations for reminder scheduling */

import type { Reminder } from '../types';

export const REMINDER_OPTIONS = [
  { label: '1 day before', value: 'day_before', hoursBefore: 24 },
  { label: '6 hours before', value: 'six_hours', hoursBefore: 6 },
  { label: '1 hour before', value: 'one_hour', hoursBefore: 1 },
  { label: '15 minutes before', value: 'fifteen_min', hoursBefore: 0.25 },
] as const;

export function computeRemindAt(eventDate: string, hoursBefore: number): string {
  const d = new Date(eventDate);
  d.setHours(d.getHours() - hoursBefore);
  return d.toISOString();
}

export function findReminderForEvent(reminders: Map<string, Reminder>, eventId: string): Reminder | undefined {
  return reminders.get(eventId);
}

export function formatReminderLabel(type: string): string {
  return REMINDER_OPTIONS.find((o) => o.value === type)?.label ?? type;
}
