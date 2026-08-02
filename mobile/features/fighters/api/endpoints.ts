/** Fighters API endpoints */
export const fighterEndpoints = {
  list: (weightClass?: string) => weightClass
    ? `/v1/fighters?weight_class=${encodeURIComponent(weightClass)}&limit=50`
    : '/v1/fighters?limit=50',
  detail: (id: string) => `/v1/fighters/${id}`,
  stats: (id: string) => `/v1/fighters/${id}/stats`,
  history: (id: string) => `/v1/fighters/${id}/fights`,
  predictions: (id: string) => `/v1/predictions/fighter/${id}`,
  similar: (id: string) => `/v1/fighters/${id}/similar?limit=10`,
  favorite: (id: string) => `/v1/favorites/fighters/${id}`,
  favorites: '/v1/favorites/fighters',
  search: (q: string) => `/v1/fighters?search=${encodeURIComponent(q)}`,
} as const;
