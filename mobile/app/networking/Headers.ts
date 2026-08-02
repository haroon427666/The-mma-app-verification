/** HTTP Headers — default and factory helpers */
export const defaultHeaders = {
  JSON: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
  FORM: { 'Content-Type': 'multipart/form-data' },
  FORM_URLENCODED: { 'Content-Type': 'application/x-www-form-urlencoded' },
} as const;

export function createHeaders(extra: Record<string, string> = {}): Record<string, string> {
  return { ...defaultHeaders.JSON, ...extra };
}

export function authHeader(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}
