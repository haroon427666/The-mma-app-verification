/** Predictions Repository — typed data access layer */

import { predictionsApi } from '../api/predictions.api';
import type {
  FightPrediction, PredictionAccuracyStats, PredictionHistoryEntry,
  PredictionFactor, MonteCarloResult, PredictionOdds,
} from '../types';

export const predictionsRepo = {
  forFight: async (fightId: string) => {
    const { data } = await predictionsApi.forFight(fightId);
    return data as FightPrediction;
  },
  forEvent: async (eventId: string) => {
    const { data } = await predictionsApi.forEvent(eventId);
    return (data ?? {}) as Record<string, FightPrediction>;
  },
  dashboard: async () => {
    const { data } = await predictionsApi.dashboard();
    return (data?.data ?? data) as { upcoming: FightPrediction[]; spotlight: FightPrediction | null };
  },
  highlights: async (limit = 8) => {
    const { data } = await predictionsApi.highlights(limit);
    return (data?.data ?? data) as FightPrediction[];
  },
  history: async (page = 1, limit = 20) => {
    const { data } = await predictionsApi.history(page, limit);
    return (data?.data ?? data) as PredictionHistoryEntry[];
  },
  accuracy: async () => {
    const { data } = await predictionsApi.accuracy();
    return (data?.data ?? data) as PredictionAccuracyStats;
  },
  matchup: async (fAId: string, fBId: string) => {
    const { data } = await predictionsApi.matchup(fAId, fBId);
    return data as FightPrediction;
  },
  monteCarlo: async (fightId: string) => {
    const { data } = await predictionsApi.monteCarlo(fightId);
    return (data?.data ?? data) as MonteCarloResult;
  },
  factors: async (fightId: string) => {
    const { data } = await predictionsApi.factors(fightId);
    return (data?.data ?? data) as PredictionFactor[];
  },
  odds: async (fightId: string) => {
    const { data } = await predictionsApi.odds(fightId);
    return (data?.data ?? data) as PredictionOdds;
  },
  save: async (fightId: string) => { await predictionsApi.save(fightId); },
  unsave: async (fightId: string) => { await predictionsApi.unsave(fightId); },
  saved: async () => {
    const { data } = await predictionsApi.saved();
    return (data?.data ?? data) as FightPrediction[];
  },
  share: async (fightId: string) => {
    const { data } = await predictionsApi.share(fightId);
    return data as { url: string; imageUrl: string };
  },
};
