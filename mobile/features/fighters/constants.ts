/** Fighters constants */

export const WEIGHT_CLASSES = [
  'Heavyweight', 'Light Heavyweight', 'Middleweight', 'Welterweight',
  'Lightweight', 'Featherweight', 'Bantamweight', 'Flyweight',
  "Women's Bantamweight", "Women's Flyweight", "Women's Strawweight",
] as const;

export const FIGHTER_STALE_TIME = 10 * 60 * 1000;
export const FIGHTERS_PAGE_SIZE = 50;
