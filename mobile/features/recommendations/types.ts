/** Recommendations module — complete types */

import type { Fighter, Event, Fight } from '../../models';

// ── Core Recommendation ──
export interface Recommendation {
  id: string;
  type: 'fighter' | 'event' | 'fight';
  entityId: string;
  name: string;
  score: number;
  reasons: RecommendationReason[];
  imageUrl: string | null;
  subtitle: string | null;
  weightClass: string | null;
  record: string | null;
}

export interface RecommendationReason {
  reason: string;
  signal: SignalType;
  weight: number;
}

export type SignalType =
  | 'followed_fighter'
  | 'watched_event'
  | 'similar_style'
  | 'weight_class_preference'
  | 'promotion_preference'
  | 'trending'
  | 'hidden_gem'
  | 'collaborative'
  | 'content_based'
  | 'popular';

// ── Dashboard ──
export interface RecommendationsDashboard {
  forYou: Recommendation[];
  becauseYouFollow: Recommendation[];
  becauseYouWatched: Recommendation[];
  trending: Recommendation[];
  similarFighters: Recommendation[];
  similarEvents: Recommendation[];
  hiddenGems: Recommendation[];
  recentlyViewed: Recommendation[];
}

// ── Evaluation Metrics ──
export interface RecommendationMetrics {
  precisionAtK: Record<string, number>;
  recallAtK: Record<string, number>;
  ndcg: number;
  mrr: number;
  diversity: number;
  coverage: number;
  novelty: number;
}

// ── Filters ──
export type RecommendationCategory =
  | 'for_you'
  | 'because_you_follow'
  | 'because_you_watched'
  | 'trending'
  | 'similar'
  | 'hidden_gems';

export type RecommendationSort = 'score' | 'recent' | 'popular';
