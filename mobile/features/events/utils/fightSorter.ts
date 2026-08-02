/** Fight sorter — Card order: Main Event → Co-Main → Main Card → Prelims → Early Prelims */

import type { FightCardEntry } from '../types';

const SEGMENT_ORDER: Record<string, number> = {
  main: 0, 'co-main': 1, mainCard: 2, prelims: 3, earlyPrelims: 4,
};

export function sortFightCard(fights: FightCardEntry[]): FightCardEntry[] {
  return [...fights].sort((a, b) => {
    const segDiff = (SEGMENT_ORDER[a.cardSegment] ?? 99) - (SEGMENT_ORDER[b.cardSegment] ?? 99);
    if (segDiff !== 0) return segDiff;
    return a.order - b.order;
  });
}

export function groupBySegment(fights: FightCardEntry[]): Record<string, FightCardEntry[]> {
  const groups: Record<string, FightCardEntry[]> = {};
  for (const f of sortFightCard(fights)) {
    const key = f.cardSegment || 'other';
    if (!groups[key]) groups[key] = [];
    groups[key].push(f);
  }
  return groups;
}

export function getMainEvent(fights: FightCardEntry[]): FightCardEntry | undefined {
  return fights.find((f) => f.isMainEvent);
}
