/** Rankings Repository — typed data access */

import { rankingsApi } from '../api/rankings.api';
import type { P4PRanking, Division, GOATEntry, ProspectEntry, RankingMovement, FighterStreak } from '../types';

export const rankingsRepo = {
  p4p: async () => { const { data } = await rankingsApi.p4p(); return (data?.data ?? data) as P4PRanking[]; },
  byDivision: async (division: string) => { const { data } = await rankingsApi.byDivision(division); return (data?.data ?? data) as Division; },
  list: async (params?: Parameters<typeof rankingsApi.list>[0]) => { const { data } = await rankingsApi.list(params); return (data?.data ?? data); },
  goat: async () => { const { data } = await rankingsApi.goat(); return (data?.data ?? data) as GOATEntry[]; },
  prospects: async (division?: string) => { const { data } = await rankingsApi.prospects(division); return (data?.data ?? data) as ProspectEntry[]; },
  movement: async (params?: Parameters<typeof rankingsApi.movement>[0]) => { const { data } = await rankingsApi.movement(params); return (data?.data ?? data) as RankingMovement[]; },
  streaks: async () => { const { data } = await rankingsApi.streaks(); return (data?.data ?? data) as FighterStreak[]; },
  champions: async () => { const { data } = await rankingsApi.champions(); return (data?.data ?? data); },
  titleDefenses: async () => { const { data } = await rankingsApi.titleDefenses(); return (data?.data ?? data); },
};
