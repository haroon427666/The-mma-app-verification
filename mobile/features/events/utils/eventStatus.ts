/** Event status utilities */

import type { ExtendedEvent } from '../types';

export function isLive(event: ExtendedEvent | null): boolean {
  return event?.status === 'LIVE' || event?.status === 'IN_PROGRESS' || event?.isLive === true;
}

export function isUpcoming(event: ExtendedEvent | null): boolean {
  return event?.status === 'SCHEDULED';
}

export function isCompleted(event: ExtendedEvent | null): boolean {
  return event?.status === 'COMPLETED' || event?.isCompleted === true;
}

export function eventStatusLabel(event: ExtendedEvent | null): string {
  if (!event) return 'Unknown';
  if (isLive(event)) return '🔴 LIVE';
  if (isCompleted(event)) return 'Completed';
  return 'Upcoming';
}

export function canWatchlist(event: ExtendedEvent | null): boolean {
  return isUpcoming(event) || isLive(event);
}
