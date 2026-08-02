/** Home feature — types */

import type { Event, Fighter, Fight, Ranking } from '../../models';

export interface HomeSection {
  id: string;
  title: string;
  type: 'live' | 'upcoming' | 'trending' | 'recommended' | 'titleFights' | 'predictions' | 'rankings';
  data: unknown[];
}

export interface HomeState {
  dismissedCards: Set<string>;
  selectedPromotion: string | null;
  scrollPosition: number;
  lastRefreshAt: string | null;
}
