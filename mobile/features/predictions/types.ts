/** Predictions module — complete domain types */

export interface FightPrediction {
  id: string;
  fightId: string;
  eventId: string;
  fighterA: FighterBrief;
  fighterB: FighterBrief;
  probA: number;
  probB: number;
  confidence: Confidence;
  finish: FinishProbability;
  rounds: RoundDistribution;
  methods: MethodDistribution;
  monteCarlo: MonteCarloResult;
  keyFactors: PredictionFactor[];
  styleMatchup: StyleMatchup | null;
  odds: PredictionOdds | null;
  createdAt: string;
}

export interface FighterBrief {
  id: string;
  fullName: string;
  record: string;
  rank: number | null;
  eloRating: number | null;
  streak: number;
  country: string | null;
}

export interface Confidence {
  score: number;
  level: ConfidenceLevel;
  breakdown: Record<string, number>;
}

export type ConfidenceLevel = 'very_high' | 'high' | 'medium' | 'low' | 'coin_flip';

export interface FinishProbability {
  koTko: number;
  submission: number;
  decision: number;
}

export interface RoundDistribution {
  round1: number;
  round2: number;
  round3: number;
  round4: number;
  round5: number;
}

export interface MethodDistribution {
  koPunch: number;
  koKnee: number;
  koHeadKick: number;
  tkoGround: number;
  rnc: number;
  guillotine: number;
  armbar: number;
  triangle: number;
  dArce: number;
  ud: number;
  sd: number;
}

export interface MonteCarloResult {
  simulations: number;
  probA: number;
  probB: number;
  stdDev: number;
  confidenceInterval95: { lower: number; upper: number };
  mostLikelyRound: number;
  roundDistribution: Record<string, number>;
}

export interface PredictionFactor {
  factor: string;
  impact: number;
  favors: 'fighter_a' | 'fighter_b';
  category: FactorCategory;
  explanation: string;
}

export type FactorCategory = 'striking' | 'grappling' | 'experience' | 'physical' | 'momentum' | 'stylistic';

export interface StyleMatchup {
  archetype: string;
  strikerAdvantage: string | null;
  grapplerAdvantage: string | null;
  styleContrast: number;
  dimensions: StyleDimension[];
}

export interface StyleDimension {
  name: string;
  valueA: number;
  valueB: number;
  edge: 'fighter_a' | 'fighter_b' | 'even';
}

export interface PredictionOdds {
  fighterA: string;
  fighterB: string;
  source: string;
  impliedProbA: number;
  impliedProbB: number;
  valueA: number | null;
  valueB: number | null;
}

export interface PredictionAccuracyStats {
  overall: number;
  last10: number;
  last50: number;
  highConfidence: number;
  veryHighConfidence: number;
  logLoss: number;
  brierScore: number;
  calibrated: boolean;
  byConfidenceLevel: Record<ConfidenceLevel, number>;
}

export interface PredictionHistoryEntry {
  id: string;
  prediction: FightPrediction;
  actual: ActualResult;
  correct: boolean;
  predictedProb: number;
  error: number;
}

export interface ActualResult {
  winnerId: string;
  method: string;
  round: number;
  time: string;
}

export type PredictionView = 'dashboard' | 'upcoming' | 'live' | 'history' | 'saved';
export type PredictionSort = 'confidence' | 'date' | 'value' | 'probability';
