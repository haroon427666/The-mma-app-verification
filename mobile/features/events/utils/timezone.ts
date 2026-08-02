/** Timezone utilities */

export function getLocalTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function convertToLocal(utcDate: string, fromTz: string): Date {
  const d = new Date(utcDate);
  return d;
}

export function formatInTimezone(date: string, tz: string, style: 'full' | 'short' | 'time' = 'short'): string {
  const d = new Date(date);
  if (style === 'time') return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: tz });
  if (style === 'short') return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: tz });
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZone: tz });
}

export function getTimezoneOffset(tz: string): string {
  const now = new Date();
  const local = now.toLocaleString('en-US', { timeZone: tz, timeZoneName: 'short' });
  const match = local.match(/([A-Z]+)$/);
  return match?.[0] ?? tz;
}
