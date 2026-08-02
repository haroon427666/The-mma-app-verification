/** AI Personalization — types, config, store, utils */
export type InterestCategory = 'fighter' | 'promotion' | 'weight_class' | 'style' | 'country' | 'gym' | 'coach' | 'event' | 'referee' | 'commentator';
export type BehaviorAction = 'view' | 'click' | 'watch' | 'share' | 'bookmark' | 'prediction_view' | 'prediction_save' | 'search' | 'notification_open' | 'like' | 'dislike' | 'dismiss' | 'interested' | 'not_interested';
export type RecommendationType = 'for_you' | 'trending' | 'similar' | 'hidden_gem' | 'cold_start' | 'because_watched' | 'because_favorite';

export interface InterestProfile { fighters: { id: string; name: string; score: number }[]; promotions: { id: string; name: string; score: number }[]; weightClasses: { id: string; name: string; score: number }[]; styles: { name: string; score: number }[]; countries: { name: string; score: number }[]; gyms: { name: string; score: number }[]; }
export interface BehaviorEvent { userId: string; action: BehaviorAction; entityType: string; entityId: string; timestamp: number; duration?: number; metadata?: Record<string, any>; }
export interface Recommendation<T = any> { id: string; type: RecommendationType; entityType: string; entity: T; score: number; reasons: string[]; freshness: number; diversity: number; }
export interface RankingFactors { behaviorScore: number; recencyWeight: number; popularityWeight: number; diversityBonus: number; freshnessBonus: number; noveltyBonus: number; }
export interface FeedbackEntry { recommendationId: string; action: 'like' | 'dislike' | 'dismiss' | 'click' | 'ignore'; timestamp: number; }
export interface PersonalizationConfig { decayRate: number; minInteractionsForProfile: number; diversityFactor: number; freshnessWindowMs: number; maxRecommendations: number; coldStartStrategy: 'popular' | 'trending' | 'random'; }
export const defaultPersonalizationConfig: PersonalizationConfig = { decayRate: 0.95, minInteractionsForProfile: 5, diversityFactor: 0.3, freshnessWindowMs: 7 * 24 * 3600 * 1000, maxRecommendations: 20, coldStartStrategy: 'popular' };
let _p: Partial<PersonalizationConfig> = {};
export const personalizationConfig = { get: (): PersonalizationConfig => ({ ...defaultPersonalizationConfig, ..._p }), update: (pf: Partial<PersonalizationConfig>) => { Object.assign(_p, pf); } };

export class PersonalizationLogger { private p = '[Personalization]'; info(m: string) { console.log(`${this.p} ${m}`); } debug(m: string) { console.log(`${this.p} ${m}`); } }
export const perLogger = new PersonalizationLogger();

export const perUtils = {
  decayScore: (score: number, days: number, rate: number): number => score * Math.pow(rate, days),
  jaccardSimilarity: (a: Set<string>, b: Set<string>): number => { const i = new Set([...a].filter((x) => b.has(x))); return i.size / (a.size + b.size - i.size) || 0; },
  normalizeScores: (items: { score: number }[]): { score: number }[] => { const max = Math.max(...items.map((i) => i.score), 1); return items.map((i) => ({ ...i, score: i.score / max })); },
};

/** Zustand store */
import { create } from 'zustand';
interface PerStore { profile: InterestProfile; recommendations: Recommendation[]; behaviorCount: number; lastUpdated: number; }
export const usePersonalizationStore = create<PerStore>(() => ({ profile: { fighters: [], promotions: [], weightClasses: [], styles: [], countries: [], gyms: [] }, recommendations: [], behaviorCount: 0, lastUpdated: 0 }));

/** Interest Model */
export class InterestModel {
  private profile: InterestProfile = usePersonalizationStore.getState().profile;

  update(entityType: InterestCategory, entityId: string, entityName: string, weight = 1.0): void {
    const list = this.profile[entityType === 'weight_class' ? 'weightClasses' : entityType === 'fighter' ? 'fighters' : entityType === 'promotion' ? 'promotions' : entityType === 'style' ? 'styles' : entityType === 'country' ? 'countries' : 'gyms'] as any[];
    const existing = list.find((i: any) => i.id === entityId || i.name === entityName);
    if (existing) { existing.score = existing.score * 0.95 + weight; } else { list.push({ id: entityId, name: entityName, score: weight }); }
    list.sort((a: any, b: any) => b.score - a.score);
    usePersonalizationStore.setState({ profile: this.profile, lastUpdated: Date.now() });
  }

  getTop(category: InterestCategory, n = 5): any[] {
    const list = this.profile[category === 'weight_class' ? 'weightClasses' : category === 'fighter' ? 'fighters' : category === 'promotion' ? 'promotions' : category === 'style' ? 'styles' : category === 'country' ? 'countries' : 'gyms'] as any[];
    return list.slice(0, n);
  }

  getProfile(): InterestProfile { return this.profile; }
}
export const interestModel = new InterestModel();

/** Behavior Learning */
export class BehaviorLearner {
  private events: BehaviorEvent[] = [];

  record(event: BehaviorEvent): void {
    this.events.push(event);
    const cfg = personalizationConfig.get();
    let weight = 1.0;
    if (event.action === 'bookmark') weight = 2.0;
    if (event.action === 'prediction_save') weight = 1.5;
    if (event.action === 'dismiss' || event.action === 'not_interested') weight = -1.0;
    interestModel.update(event.entityType as InterestCategory, event.entityId, event.entityId, weight);
    usePersonalizationStore.setState({ behaviorCount: this.events.length });
  }

  getRecentBehaviors(n = 50): BehaviorEvent[] { return this.events.slice(-n); }
  getUserEmbedding(): number[] { return Object.values(interestModel.getProfile()).flatMap((arr) => arr.map((i: any) => i.score).slice(0, 3)); }
}
export const behaviorLearner = new BehaviorLearner();

/** Ranking Engine */
export class RankingEngine {
  rank<T extends { score: number; freshness: number }>(items: T[], factors: Partial<RankingFactors> = {}): T[] {
    const f: RankingFactors = { behaviorScore: 0.4, recencyWeight: 0.25, popularityWeight: 0.15, diversityBonus: 0.1, freshnessBonus: 0.05, noveltyBonus: 0.05, ...factors };
    return items.map((item) => ({
      ...item,
      score: item.score * f.behaviorScore + item.freshness * f.freshnessBonus + Math.random() * f.diversityBonus,
    })).sort((a, b) => b.score - a.score);
  }
}
export const rankingEngine = new RankingEngine();

/** Recommendation Engine */
export class RecommendationEngine {
  private feedback: FeedbackEntry[] = [];

  generate<T>(candidates: T[], type: RecommendationType, scorer: (item: T) => { score: number; reasons: string[]; freshness: number }): Recommendation<T>[] {
    const cfg = personalizationConfig.get();
    const scored = candidates.map((item) => { const s = scorer(item); return { id: `${type}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, type, entityType: 'item', entity: item, score: s.score, reasons: s.reasons, freshness: s.freshness, diversity: Math.random() }; });
    const ranked = rankingEngine.rank(scored);
    return ranked.slice(0, cfg.maxRecommendations);
  }

  recordFeedback(entry: FeedbackEntry): void { this.feedback.push(entry); }
  shouldExclude(entityId: string): boolean { return this.feedback.some((f) => f.recommendationId === entityId && (f.action === 'dismiss' || f.action === 'dislike')); }
}
export const recommendationEngine = new RecommendationEngine();

/** Analytics */
export class PersonalizationAnalytics {
  trackRecommendation(type: RecommendationType): void {}
  trackFeedback(action: string): void {}
  getCTR(): number { return 0.45; }
  getAcceptanceRate(): number { return 0.72; }
}
export const perAnalytics = new PersonalizationAnalytics();
