/** Fighters API endpoints */
export const fighterEndpoints = {
  list: (weightClass?: string) => weightClass
    ? `/v1/fighters?weight_class=${encodeURIComponent(weightClass)}&limit=50`
    : '/v1/fighters?limit=50',
  detail: (id: string) => `/v1/fighters/${id}`,
  stats: (id: string) => `/v1/fighters/${id}/statistics`,
  history: (id: string) => `/v1/fighters/${id}/history`,
  similar: (id: string) => `/v1/fighters/${id}/similar?limit=10`,
  favorite: (id: string) => `/v1/me/favorites/fighters/${id}`,
  favorites: '/v1/me/favorites',
  search: (q: string) => `/v1/fighters?search=${encodeURIComponent(q)}`,
} as const;
