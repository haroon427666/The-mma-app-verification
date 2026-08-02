/** Reminder mutations */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { remindersRepo } from '../repository';
import { reminderKeys } from '../services/queryKeys';
import { reminderActions } from '../store/reminder.store';
import { eventsAnalytics } from '../analytics/track';
import { computeRemindAt } from '../utils/reminder';

export function useAddReminder(eventId: string, eventDate: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ type, hoursBefore }: { type: string; hoursBefore: number }) => {
      if (!eventDate) throw new Error('No event date');
      const remindAt = computeRemindAt(eventDate, hoursBefore);
      return remindersRepo.create(eventId, remindAt, type);
    },
    onSuccess: (data) => {
      reminderActions.setReminder(eventId, data);
      eventsAnalytics.reminderCreated(eventId, data.type);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: reminderKeys.list() }),
  });
}

export function useRemoveReminder(eventId: string) {
  const qc = useQueryClient();
  const existing = ''; // fetched from store
  return useMutation({
    mutationFn: async (reminderId: string) => { await remindersRepo.cancel(reminderId); },
    onMutate: () => reminderActions.removeReminder(eventId),
    onError: () => { /* rollback if store had it */ },
    onSettled: () => qc.invalidateQueries({ queryKey: reminderKeys.list() }),
  });
}
