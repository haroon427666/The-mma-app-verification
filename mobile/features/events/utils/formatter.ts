/** Formatters — event dates, fight records, and display values */

export function formatEventDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
}

export function formatEventTime(date: string): string {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: 'numeric', minute: '2-digit',
  });
}

export function formatVenue(venue: string, city: string, country: string): string {
  return [venue, city, country].filter(Boolean).join(' • ');
}

export function formatBroadcasters(broadcasters: string[]): string {
  if (!broadcasters?.length) return 'TBA';
  return broadcasters.join(' / ');
}

export function formatMethod(method: string, detail: string): string {
  if (!method) return '';
  if (method === 'KO/TKO' && detail) return `KO/TKO (${detail})`;
  if (method === 'Submission' && detail) return `Submission (${detail})`;
  return method;
}

export function formatResult(winner: string, method: string, round: number, time: string): string {
  if (!winner) return 'TBD';
  return `${winner} def. by ${method} R${round} ${time}`;
}
