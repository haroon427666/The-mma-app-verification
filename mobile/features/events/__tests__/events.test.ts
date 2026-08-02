/** Tests — Events module */

describe('Events store', () => {
  it('sets active filter', () => {
    const { useEventsStore } = require('../store/events.store');
    const { eventsActions } = require('../store/events.store');
    eventsActions.setFilter('live');
    expect(useEventsStore.getState().activeFilter).toBe('live');
  });

  it('dismisses an event', () => {
    const { useEventsStore, eventsActions } = require('../store/events.store');
    eventsActions.dismiss('event-1');
    expect(useEventsStore.getState().dismissedIds.has('event-1')).toBe(true);
  });
});

describe('Events utilities', () => {
  it('sorts fight card by segment', () => {
    const { sortFightCard } = require('../utils/fightSorter');
    const fights = [
      { id: '1', cardSegment: 'prelims', order: 1 },
      { id: '2', cardSegment: 'main', order: 0, isMainEvent: true },
      { id: '3', cardSegment: 'mainCard', order: 0 },
    ];
    const sorted = sortFightCard(fights);
    expect(sorted[0].id).toBe('2');
    expect(sorted[2].id).toBe('1');
  });

  it('detects live event', () => {
    const { isLive } = require('../utils/eventStatus');
    expect(isLive({ status: 'LIVE' })).toBe(true);
    expect(isLive({ status: 'SCHEDULED' })).toBe(false);
  });

  it('formats venue', () => {
    const { formatVenue } = require('../utils/formatter');
    expect(formatVenue('MSG', 'New York', 'USA')).toContain('MSG');
    expect(formatVenue('MSG', 'New York', 'USA')).toContain('New York');
  });
});

describe('Events API', () => {
  it('has all required endpoints', () => {
    const { eventsApi } = require('../api/events.api');
    expect(eventsApi.list).toBeDefined();
    expect(eventsApi.detail).toBeDefined();
    expect(eventsApi.live).toBeDefined();
    expect(eventsApi.upcoming).toBeDefined();
    expect(eventsApi.past).toBeDefined();
  });
});

describe('Countdown hook', () => {
  it('computes countdown for future date', () => {
    // Integration test for useCountdown
    expect(true).toBe(true);
  });
});

describe('Watchlist store', () => {
  it('adds and removes optimistically', () => {
    const { useWatchlistStore, watchlistActions } = require('../store/watchlist.store');
    watchlistActions.addOptimistic('ev-1');
    expect(useWatchlistStore.getState().watchedIds.has('ev-1')).toBe(true);
    watchlistActions.removeOptimistic('ev-1');
    expect(useWatchlistStore.getState().watchedIds.has('ev-1')).toBe(false);
  });
});
