/** useReminder — create/cancel reminders for an event */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { remindersApi } from '../api/reminders.api';
import { useReminderStore, reminderActions } from '../store/reminder.store';
import { computeRemindAt } from '../utils/reminder';
import type { Reminder } from '../types';

export function useReminder(eventId: string, eventDate: string | null) {
  const qc = useQueryClient();
  const { reminders } = useReminderStore();
  const existing = reminders.get(eventId);

  const listQuery = useQuery({
    queryKey: ['reminders'],
    queryFn: async () => { const { data } = await remindersApi.list(); return data.data ?? []; },
    staleTime: 60 * 1000,
  });

  const create = useMutation({
    mutationFn: async ({ type, hoursBefore }: { type: string; hoursBefore: number }) => {
      if (!eventDate) throw new Error('No event date');
      const remindAt = computeRemindAt(eventDate, hoursBefore);
      const { data } = await remindersApi.create(eventId, remindAt, type);
      return data as Reminder;
    },
    onSuccess: (data) => reminderActions.setReminder(eventId, data),
    onSettled: () => qc.invalidateQueries({ queryKey: ['reminders'] }),
  });

  const cancel = useMutation({
    mutationFn: async () => {
      if (existing) await remindersApi.cancel(existing.id);
    },
    onMutate: () => reminderActions.removeReminder(eventId),
    onError: () => { if (existing) reminderActions.setReminder(eventId, existing); },
    onSettled: () => qc.invalidateQueries({ queryKey: ['reminders'] }),
  });

  return {
    existing,
    create: create.mutate,
    cancel: cancel.mutate,
    isCreating: create.isPending,
    isCancelling: cancel.isPending,
  };
}
