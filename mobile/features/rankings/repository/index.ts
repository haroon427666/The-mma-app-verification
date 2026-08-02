/** Rankings Repository — typed data access */

import { rankingsApi } from '../api/rankings.api';
import type { P4PRanking, Division, RankingHistoryPoint, GOATEntry, ProspectEntry, RankingMovement, FighterStreak, ChampionRecord } from '../types';

export const rankingsRepo = {
  p4p: async () => { const { data } = await rankingsApi.p4p(); return (data?.data ?? data) as P4PRanking[]; },
  byDivision: async (division: string) => { const { data } = await rankingsApi.byDivision(division); return (data?.data ?? data) as Division; },
  list: async (params?: Parameters<typeof rankingsApi.list>[0]) => { const { data } = await rankingsApi.list(params); return (data?.data ?? data); },
  history: async (fighterId: string) => { const { data } = await rankingsApi.history(fighterId); return (data?.data ?? data) as RankingHistoryPoint[]; },
  goat: async () => { const { data } = await rankingsApi.goat(); return (data?.data ?? data) as GOATEntry[]; },
  prospects: async (division?: string) => { const { data } = await rankingsApi.prospects(division); return (data?.data ?? data) as ProspectEntry[]; },
  movement: async (params?: Parameters<typeof rankingsApi.movement>[0]) => { const { data } = await rankingsApi.movement(params); return (data?.data ?? data) as RankingMovement[]; },
  streaks: async () => { const { data } = await rankingsApi.streaks(); return (data?.data ?? data) as FighterStreak[]; },
  champions: async () => { const { data } = await rankingsApi.champions(); return (data?.data ?? data); },
  championsHistory: async (wc?: string) => { const { data } = await rankingsApi.championsHistory(wc); return (data?.data ?? data) as ChampionRecord[]; },
  titleDefenses: async () => { const { data } = await rankingsApi.titleDefenses(); return (data?.data ?? data); },
  elo: async (params?: Parameters<typeof rankingsApi.elo>[0]) => { const { data } = await rankingsApi.elo(params); return (data?.data ?? data); },
  composite: async (params?: Parameters<typeof rankingsApi.composite>[0]) => { const { data } = await rankingsApi.composite(params); return (data?.data ?? data); },
};
