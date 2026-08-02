/** Hooks — updated to use repository layer instead of raw API */

import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { eventsRepo, fightsRepo, predictionsRepo } from '../repository';
import { eventKeys, fightKeys, predictionKeys } from '../services/queryKeys';
import { useEventsStore } from '../store/events.store';
import type { FightPrediction } from '../types';

// Re-export all hooks with repository-based implementations
export { useLiveEvents, useUpcomingEvents, usePastEvents, useFightCard, useCountdown, useWatchlist, useReminder, usePredictions } from './index';
