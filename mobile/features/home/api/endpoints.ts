/** Home feature — API endpoints, queries, mutations */

export const homeEndpoints = {
  live: '/v1/events/live?limit=5',
  upcoming: '/v1/events/upcoming?limit=5',
  recommendedFighters: '/v1/recommendations/fighters?limit=6',
  titleFights: '/v1/fights?is_title=true&status=SCHEDULED&limit=5',
} as const;
