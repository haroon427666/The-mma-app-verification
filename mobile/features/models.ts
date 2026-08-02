/** Shared domain models consumed by all features */

export interface Fighter {
  id: string;
  fullName: string;
  firstName: string;
  lastName: string;
  nickname: string | null;
  headshotUrl: string | null;
  imageUrl: string | null;
  weightClass: string | null;
  stance: string | null;
  heightCm: number | null;
  reachCm: number | null;
  age: number | null;
  nationality: string | null;
  team: string | null;
  record: string;
  wins: number;
  losses: number;
  draws: number;
  koWins: number;
  subWins: number;
  latestRank: number | null;
  isChampion: boolean;
  streak: number;
  eloRating: number | null;
  finishRate: number;
  momentumScore: number | null;
  winQuality: number | null;
  championshipScore: number | null;
  stats: FighterStats | null;
  embedding: number[] | null;
}

export interface FighterStats {
  sigStrikesLandedPerMin: number;
  sigStrikesAccuracyPct: number;
  sigStrikesAbsorbedPerMin: number;
  sigStrikesDefensePct: number;
  takedownAvgPer15: number;
  takedownAccuracyPct: number;
  takedownDefensePct: number;
  submissionAvgPer15: number;
  knockdownsTotal: number;
  avgFightTimeSec: number;
}

export interface Event {
  id: string;
  name: string;
  shortName: string;
  date: string;
  endDate: string | null;
  timezone: string;
  venue: string;
  city: string;
  country: string;
  promotion: string;
  promotionLogo: string | null;
  bannerUrl: string | null;
  posterUrl: string | null;
  thumbnailUrl: string | null;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'LIVE' | 'COMPLETED' | 'CANCELLED';
  fightCount: number;
  broadcasters: string[];
  isLive: boolean;
}

export interface Fight {
  id: string;
  eventId: string;
  eventName: string;
  order: number;
  cardSegment: string;
  weightClass: string;
  isTitleFight: boolean;
  isMainEvent: boolean;
  fighterAId: string;
  fighterAName: string;
  fighterARecord: string;
  fighterARank: number | null;
  fighterBId: string;
  fighterBName: string;
  fighterBRecord: string;
  fighterBRank: number | null;
  result: string | null;
  winnerId: string | null;
  method: string | null;
  round: number | null;
  time: string | null;
  rounds: number;
  status: string;
}

export interface Ranking {
  id: string;
  weightClass: string;
  gender: 'men' | 'women';
  rank: number;
  fighter: Fighter;
  previousRank: number | null;
  movement: 'up' | 'down' | 'steady' | 'new';
  isChampion: boolean;
}

export interface Prediction {
  fighterA: string;
  fighterB: string;
  probA: number;
  probB: number;
  confidence: { score: number; level: string; factors: Record<string, number> };
  finish: { koTko: number; submission: number; decision: number };
  rounds: Record<string, number>;
  methods: Record<string, number>;
  monteCarlo: { probA: number; probB: number; confidenceInterval95: { lower: number; upper: number }; mostLikelyRound: number } | null;
  keyFactors: Array<{ factor: string; impact: number; favors: string }>;
  styleAnalysis: { archetype: string; strikerAdvantage: string; grapplerAdvantage: string; styleContrast: number } | null;
}

export interface Recommendation {
  id: string;
  name: string;
  type: 'fighter' | 'event' | 'fight';
  score: number;
  reasons: string[];
  imageUrl: string | null;
  weightClass: string | null;
  record: string | null;
}

export interface HomeFeed {
  liveEvents: Event[];
  upcomingEvents: Event[];
  recommendedFighters: Fighter[];
  trendingFighters: Fighter[];
  upcomingTitleFights: Fight[];
  predictionHighlights: Array<{ fight: Fight; prediction: Prediction }>;
  recentRankingChanges: Ranking[];
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  payload: Record<string, unknown> | null;
}

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  displayName: string | null;
  avatarUrl: string | null;
  role: string;
  emailVerified: boolean;
  createdAt: string;
  preferences: {
    theme: string;
    timezone: string;
    defaultHomepage: string;
    defaultWeightClasses: string[];
    notifyUpcomingFight: boolean;
    notifyEventStarting: boolean;
    notifyRankingChanged: boolean;
    notifyFightCancelled: boolean;
  };
}
