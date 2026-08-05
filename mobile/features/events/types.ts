/** Events module — complete type definitions */

import type { Fighter, Fight as BaseFight, Event as BaseEvent } from '../models';

export interface ExtendedEvent extends BaseEvent {
  promotion: string;
  promotionLogo: string | null;
  bannerUrl: string | null;
  posterUrl: string | null;
  thumbnailUrl: string | null;
  venue: string;
  city: string;
  country: string;
  timezone: string;
  broadcasters: string[];
  fightCount: number;
  isLive: boolean;
  isCompleted: boolean;
  startTime: string;
  endTime: string | null;
  fights: FightCardEntry[];
  results?: FightResult[];
  statistics?: EventStatistics;
}

export interface FightCardEntry extends Omit<BaseFight, 'result' | 'status' | 'cardSegment'> {
  order: number;
  cardSegment: CardSegment;
  weightClass: string;
  isTitleFight: boolean;
  isMainEvent: boolean;
  isCoMainEvent: boolean;
  fighterA: FighterDetail;
  fighterB: FighterDetail;
  result: FightResult | null;
  rounds: number;
  status: FightStatus;
}

export interface FighterDetail {
  id: string;
  fullName: string;
  firstName: string;
  lastName: string;
  nickname: string | null;
  country: string;
  flagCode: string;
  record: string;
  rank: number | null;
  isChampion: boolean;
  streak: number;
  eloRating: number | null;
  imageUrl: string | null;
}

export interface FightResult {
  winnerId: string;
  method: 'KO/TKO' | 'Submission' | 'Decision' | 'DQ' | 'No Contest' | 'Draw';
  methodDetail: string;
  round: number;
  time: string;
}

export type CardSegment = 'main' | 'co-main' | 'mainCard' | 'prelims' | 'earlyPrelims';
export type FightStatus = 'SCHEDULED' | 'WALKOUT' | 'IN_PROGRESS' | 'FINISHED' | 'CANCELLED';
export type EventFilter = 'live' | 'upcoming' | 'past' | 'thisWeek' | 'thisMonth' | 'calendar';

export interface EventStatistics {
  totalFights: number;
  titleFights: number;
  decisions: number;
  finishes: number;
  koTko: number;
  submissions: number;
  averageAge: number;
  countriesRepresented: number;
  weightClasses: string[];
  debuts: number;
  rankedFighters: number;
}

export interface CountdownState {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isPast: boolean;
  isLive: boolean;
  isStartingSoon: boolean;
}
