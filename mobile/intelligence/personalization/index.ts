/** AI Personalization — Hooks + index */
import { useState, useCallback, useEffect } from 'react';
import { interestModel, behaviorLearner, recommendationEngine, rankingEngine, perAnalytics, usePersonalizationStore } from './PersonalizationEngine';
import type { BehaviorAction, RecommendationType } from './PersonalizationEngine';

export function usePersonalization() {
  const { profile, recommendations, behaviorCount } = usePersonalizationStore();
  return { profile, recommendations, behaviorCount, topFighters: interestModel.getTop('fighter'), topPromotions: interestModel.getTop('promotion'), topStyles: interestModel.getTop('style') };
}

export function useBehaviorTracking() {
  const track = useCallback((action: BehaviorAction, entityType: string, entityId: string, meta?: any) => {
    behaviorLearner.record({ userId: 'current', action, entityType, entityId, timestamp: Date.now(), metadata: meta });
  }, []);
  return { track, recentBehaviors: behaviorLearner.getRecentBehaviors() };
}

export function useRecommendations<T>(entityType: string, candidates: T[], scorer: (item: T) => { score: number; reasons: string[]; freshness: number }) {
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const refresh = useCallback(async (type: RecommendationType = 'for_you') => { setLoading(true); try { const r = recommendationEngine.generate(candidates, type, scorer); setRecs(r); } finally { setLoading(false); } }, [candidates, scorer]);
  const feedback = useCallback((recId: string, action: 'like' | 'dislike' | 'dismiss') => recommendationEngine.recordFeedback({ recommendationId: recId, action, timestamp: Date.now() }), []);
  return { recommendations: recs, loading, refresh, feedback };
}

export function useInterestProfile() {
  const profile = interestModel.getProfile();
  return { profile, topFighters: () => interestModel.getTop('fighter'), topWeightClasses: () => interestModel.getTop('weight_class') };
}

/*
## AI Personalization Engine

### Architecture
```
User Action → BehaviorLearner.record({ view, click, bookmark, ... })
  → InterestModel.update(category, id, weight)
  → RecommendationEngine.generate(candidates, scorer)
  → RankingEngine.rank(scoredItems, factors)
  → Personalized feed
```

### Ranking Factors
| Factor | Weight | Description |
|---|---|---|
| behaviorScore | 0.40 | User interest model score |
| recencyWeight | 0.25 | Time decay weighting |
| popularityWeight | 0.15 | Global popularity |
| diversityBonus | 0.10 | Content variety |
| freshnessBonus | 0.05 | New content boost |
| noveltyBonus | 0.05 | Discovery incentive |

### Hooks
- usePersonalization() → profile, top fighters/promotions/styles
- useBehaviorTracking() → track views/clicks/bookmarks
- useRecommendations<T>() → generate personalized feed
- useInterestProfile() → full interest model
*/

export { interestModel, behaviorLearner, recommendationEngine, rankingEngine, perAnalytics, usePersonalizationStore, personalizationConfig, PersonalizationLogger, perLogger, perUtils } from './PersonalizationEngine';
export type { InterestCategory, BehaviorAction, RecommendationType, InterestProfile, BehaviorEvent, Recommendation, RankingFactors, FeedbackEntry, PersonalizationConfig } from './PersonalizationEngine';
