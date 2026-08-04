/** Fighters module — complete type definitions */

import type { Fighter } from '../models';

// ── Extended Fighter ──
export interface FighterProfile extends Fighter {
  // Physical
  heightCm: number | null;
  reachCm: number | null;
  legReachCm: number | null;
  apeIndex: number | null;
  age: number | null;
  dateOfBirth: string | null;
  nationality: string | null;
  birthCity: string | null;
  stance: string | null;
  
  // Career
  debut: string | null;
  yearsActive: number;
  gym: string | null;
  team: string | null;
  coach: string | null;
  
  // Record
  wins: number;
  losses: number;
  draws: number;
  noContests: number;
  koWins: number;
  subWins: number;
  decisionWins: number;
  koLosses: number;
  subLosses: number;
  decisionLosses: number;
  
  // Rankings
  latestRank: number | null;
  bestRank: number | null;
  isChampion: boolean;
  isInterimChampion: boolean;
  titleWins: number;
  titleDefenses: number;
  
  // Scores
  eloRating: number | null;
  glickoRating: number | null;
  compositeScore: number | null;
  momentumScore: number | null;
  winQuality: number | null;
  opponentQuality: number | null;
  
  // Embedding
  styleVector: number[] | null;
  embedding: number[] | null;
}

// ── Stats ──
export interface FighterStats {
  sigStrikesLandedPerMin: number;
  sigStrikesAccuracyPct: number;
  sigStrikesAbsorbedPerMin: number;
  sigStrikesDefensePct: number;
  sigStrikesHeadPct: number;
  sigStrikesBodyPct: number;
  sigStrikesLegPct: number;
  sigStrikesDistancePct: number;
  sigStrikesClinchPct: number;
  sigStrikesGroundPct: number;
  takedownAvgPer15: number;
  takedownAccuracyPct: number;
  takedownDefensePct: number;
  submissionAvgPer15: number;
  reversalsPer15: number;
  knockdownsTotal: number;
  knockdownsPerFight: number;
  avgFightTimeSec: number;
  controlTimePct: number;
  topPositionPct: number;
  bottomPositionPct: number;
}

// ── Fight History ──
export interface FightHistoryEntry {
  id: string;
  eventId: string;
  eventName: string;
  date: string;
  opponent: { id: string; name: string; record: string; rank: number | null };
  result: 'W' | 'L' | 'D' | 'NC';
  method: string;
  methodDetail: string;
  round: number;
  time: string;
  weightClass: string;
  isTitleFight: boolean;
  bonus: string | null;
}

// ── Similar Fighter ──
export interface SimilarFighter {
  fighter: FighterProfile;
  similarityScore: number;
  breakdown: Array<{ trait: string; score: number; verdict: 'similar' | 'moderate' | 'different' }>;
}

// ── Style Analysis ──
export interface StyleAnalysis {
  primaryStyle: string;
  archetype: string;
  strengths: string[];
  weaknesses: string[];
  strikingVolume: number;
  grapplingVolume: number;
  finishingAbility: number;
  pressureScore: number;
  cardioScore: number;
  durabilityScore: number;
}

// ── Comparison ──
export interface FighterComparison {
  fighterA: FighterProfile;
  fighterB: FighterProfile;
  dimensions: Array<{ label: string; valueA: number | string; valueB: number | string; edge: 'A' | 'B' | 'even' }>;
  winnerPrediction: { probA: number; probB: number; confidence: string };
  styleAnalysis: string;
}

// ── Rank History ──
export interface RankHistoryPoint {
  date: string;
  rank: number | null;
  isChampion: boolean;
  event: string | null;
}

// ── Enums ──
export type FighterFilterType = 'all' | 'ranked' | 'champions' | 'prospects' | 'byWeightClass';
export type FighterSortType = 'rank' | 'elo' | 'name_asc' | 'name_desc' | 'recent';
export type FighterTabKey = 'overview' | 'stats' | 'history' | 'predictions' | 'similar' | 'media';
