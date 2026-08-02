/** Events analytics — track every meaningful interaction */

type EventProperties = Record<string, string | number | boolean>;

const track = (event: string, props?: EventProperties) => {
  if (__DEV__) { console.log(`[analytics] ${event}`, props); return; }
  // PostHog / Amplitude / Firebase call goes here
};

export const eventsAnalytics = {
  eventOpened: (eventId: string, eventName: string) =>
    track('event_opened', { eventId, eventName }),

  fightClicked: (fightId: string, fighterA: string, fighterB: string) =>
    track('fight_clicked', { fightId, fighterA, fighterB }),

  predictionViewed: (fightId: string, probA: number, probB: number) =>
    track('prediction_viewed', { fightId, probA, probB }),

  reminderCreated: (eventId: string, type: string) =>
    track('reminder_created', { eventId, type }),

  watchlistAdded: (eventId: string) =>
    track('watchlist_added', { eventId }),

  watchlistRemoved: (eventId: string) =>
    track('watchlist_removed', { eventId }),

  eventShared: (eventId: string) =>
    track('event_shared', { eventId }),

  liveStarted: (eventId: string) =>
    track('live_event_started', { eventId }),

  resultViewed: (eventId: string, fightCount: number) =>
    track('results_viewed', { eventId, fightCount }),
};
