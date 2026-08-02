/** Home feature — API endpoints, queries, mutations */

export const homeEndpoints = {
  feed: '/v1/home',
  live: '/v1/events?status=LIVE,IN_PROGRESS&limit=5',
  upcoming: '/v1/events/upcoming?limit=5',
  trending: '/v1/fighters/trending?limit=8',
  recommendedFighters: '/v1/recommendations/fighters?limit=6',
  titleFights: '/v1/fights?is_title=true&status=SCHEDULED&limit=5',
  predictionHighlights: '/v1/predictions/highlights?limit=4',
  rankingChanges: '/v1/rankings/changes?limit=5',
} as const;
