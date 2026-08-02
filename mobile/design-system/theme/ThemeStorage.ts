/** Theme storage layer — persists user theme preference */
let cached: string | null = null;
export const ThemeStorage = {
  get: (): string => cached || 'dark',
  set: (mode: string) => { cached = mode; },
};