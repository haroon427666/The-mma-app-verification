/** Rankings module — complete type definitions */

import type { Fighter } from '../../models';

// ── Core Ranking Types ──
export interface RankingEntry {
  id: string;
  rank: number;
  previousRank: number | null;
  movement: 'up' | 'down' | 'steady' | 'new';
  fighter: RankingFighter;
  points: number | null;
  isChampion: boolean;
  isInterimChampion: boolean;
}

export interface RankingFighter extends Pick<Fighter, 'id' | 'fullName' | 'firstName' | 'lastName' | 'nickname' | 'headshotUrl' | 'imageUrl'> {
  record: string;
  wins: number; losses: number; draws: number;
  koWins: number; subWins: number;
  streak: number;
  eloRating: number | null;
  glickoRating: number | null;
  compositeScore: number | null;
  momentumScore: number | null;
  winQuality: number | null;
  strengthOfSchedule: number | null;
  championshipScore: number | null;
  ageCurve: number | null;
  trajectory: 'rising' | 'peak' | 'declining' | 'unknown';
  nationality: string | null;
  team: string | null;
}

// ── Division ──
export interface Division {
  name: string;
  gender: 'men' | 'women';
  weightLimit: number | null;
  champion: RankingFighter | null;
  interimChampion: RankingFighter | null;
  rankings: RankingEntry[];
  lastUpdated: string;
}

// ── P4P ──
export interface P4PRanking {
  rank: number;
  previousRank: number | null;
  movement: 'up' | 'down' | 'steady' | 'new';
  fighter: RankingFighter;
  division: string;
  compositeScore: number;
}

// ── Ranking History ──
export interface RankingHistoryPoint {
  date: string;
  rank: number | null;
  elo: number | null;
  composite: number | null;
  glicko: number | null;
  momentum: number | null;
  isChampion: boolean;
  event: string | null;
  opponent: string | null;
  result: string | null;
}

// ── Champion History ──
export interface ChampionRecord {
  fighter: RankingFighter;
  weightClass: string;
  wonDate: string;
  lostDate: string | null;
  defenses: number;
  reign: number; // days
}

// ── GOAT ──
export interface GOATEntry {
  rank: number;
  fighter: RankingFighter;
  compositeScore: number;
  eloPeak: number;
  titleWins: number;
  titleDefenses: number;
  finishRate: number;
  winQuality: number;
  strengthOfSchedule: number;
  divisions: string[];
  era: string;
}

// ── Prospect ──
export interface ProspectEntry {
  fighter: RankingFighter;
  age: number;
  record: string;
  finishRate: number;
  elo: number;
  trajectory: 'rising' | 'peak' | 'declining' | 'unknown';
  potential: number;
  division: string;
  comparable: string; // "similar to <fighter>"
}

// ── Movement ──
export interface RankingMovement {
  fighter: RankingFighter;
  division: string;
  fromRank: number;
  toRank: number;
  change: number; // positive = improved
  date: string;
  reason: string;
}

// ── Streak ──
export interface FighterStreak {
  fighter: RankingFighter;
  streak: number;
  type: 'win' | 'loss';
  bestRank: number | null;
  lastFight: string;
}

// ── Filters ──
export type RankingView = 'p4p' | 'division' | 'goat' | 'prospects' | 'movement';
export type SortRankingBy = 'rank' | 'elo' | 'composite' | 'momentum' | 'winQuality';
export type MovementDirection = 'up' | 'down' | 'all';

// ── Composite Score Breakdown ──
export interface CompositeBreakdown {
  elo: number;
  glicko: number;
  momentum: number;
  winQuality: number;
  strengthOfSchedule: number;
  championshipScore: number;
  ageCurve: number;
  activityScore: number;
  total: number;
}
