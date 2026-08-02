/** Accessibility labels — centralized, i18n-ready labels for screen readers */

export const eventLabels = {
  eventCard: (name: string, date: string) => `Event: ${name}, ${date}`,
  liveBanner: (name: string) => `Live event: ${name}`,
  fightRow: (a: string, b: string) => `Fight: ${a} versus ${b}`,
  countdown: (days: number, hours: number) => `Starts in ${days} days and ${hours} hours`,
  watchlistAdd: 'Add event to watchlist',
  watchlistRemove: 'Remove event from watchlist',
  reminderSet: 'Reminder is set for this event',
  reminderCreate: 'Set a reminder for this event',
  shareEvent: (name: string) => `Share event: ${name}`,
  resultsButton: 'View event results',
} as const;
