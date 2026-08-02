/** Fighters types */

import type { Fighter } from '../../models';

export interface FighterComparison {
  fighterA: Fighter;
  fighterB: Fighter | null;
}

export interface FighterTab {
  key: 'overview' | 'stats' | 'history' | 'predictions' | 'media';
  label: string;
}

export const FIGHTER_TABS: FighterTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'stats', label: 'Stats' },
  { key: 'history', label: 'History' },
  { key: 'predictions', label: 'Predictions' },
];
