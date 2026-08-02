/** Reminder store — active reminders per event */

import { create } from 'zustand';
import type { Reminder } from '../types';

interface ReminderState {
  reminders: Map<string, Reminder>;
  isCreating: boolean;
}

export const useReminderStore = create<ReminderState>(() => ({
  reminders: new Map(),
  isCreating: false,
}));

export const reminderActions = {
  setReminder: (eventId: string, reminder: Reminder) => useReminderStore.setState((s) => {
    const next = new Map(s.reminders); next.set(eventId, reminder);
    return { reminders: next };
  }),
  removeReminder: (eventId: string) => useReminderStore.setState((s) => {
    const next = new Map(s.reminders); next.delete(eventId);
    return { reminders: next };
  }),
  setCreating: (v: boolean) => useReminderStore.setState({ isCreating: v }),
};
