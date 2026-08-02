/** Fighter Scouting — types, config, store, styles, similarity, career, matchups, reports, analytics */
export type FightingStyle = 'striker' | 'grappler' | 'wrestler' | 'bjj' | 'mixed' | 'counter' | 'pressure' | 'technical';
export type StyleDimension = 'striking' | 'grappling' | 'wrestling' | 'bjj' | 'cardio' | 'fight_iq' | 'aggression' | 'defense' | 'counter_striking' | 'scrambling' | 'clinch' | 'pace';
export type CareerPhase = 'prospect' | 'rising' | 'prime' | 'peak' | 'declining' | 'veteran';
export type ReportType = 'full' | 'opponent' | 'pre_fight' | 'post_fight' | 'summary';

export interface StyleProfile { primaryStyle: FightingStyle; secondaryStyle: FightingStyle; dimensions: Record<StyleDimension, number>; signature: number[]; summary: string; }
export interface SimilarityResult { fighterId: string; name: string; similarity: number; sharedStrengths: string[]; sharedWeaknesses: string[]; }
export interface CareerProjection { currentPhase: CareerPhase; estimatedPeak: number; declineAge?: number; trajectory: 'rising' | 'stable' | 'declining'; titleProbability: number; rankingProjection: number[]; longevityYears: number; }
export interface MatchupAnalysis { advantages: string[]; disadvantages: string[]; keyExchanges: string[]; dangerAreas: string[]; expectedPace: 'fast' | 'moderate' | 'slow'; winConditions: string[]; lossConditions: string[]; overallEdge: number; }
export interface ScoutingReport { id: string; type: ReportType; fighterId: string; fighterName: string; generatedAt: number; sections: { title: string; content: string }[]; overallGrade: string; }

export class ScoutingLogger { private p = '[Scouting]'; info(m: string) { console.log(`${this.p} ${m}`); } debug(m: string) { console.log(`${this.p} ${m}`); } }
export const scoutLogger = new ScoutingLogger();

/** Style Analyzer */
export class StyleAnalyzer {
  analyze(fighter: { stats: Record<string, number>; record: { koWins: number; subWins: number; decWins: number; wins: number } }): StyleProfile {
    const r = fighter.record;
    const totalWins = Math.max(r.wins, 1);
    const koRate = r.koWins / totalWins;
    const subRate = r.subWins / totalWins;

    let primary: FightingStyle = 'mixed';
    if (koRate > 0.5) primary = 'striker';
    else if (subRate > 0.4) primary = 'grappler';
    else if (r.decWins / totalWins > 0.5) primary = 'technical';

    const dimensions: Record<StyleDimension, number> = {
      striking: koRate * 10, grappling: subRate * 10, wrestling: 6 + Math.random() * 2, bjj: subRate * 12, cardio: 7 + Math.random(), fight_iq: 7 + Math.random(), aggression: koRate > 0.5 ? 8 : 5 + Math.random(), defense: 6 + Math.random(), counter_striking: 5 + Math.random(), scrambling: subRate > 0.3 ? 7 : 5 + Math.random(), clinch: 6 + Math.random(), pace: 7 + Math.random(),
    };

    const signature = Object.values(dimensions);
    return { primaryStyle: primary, secondaryStyle: primary === 'striker' ? 'pressure' : 'mixed', dimensions, signature, summary: `${primary} fighter with ${subRate > 0.3 ? 'strong ground game' : 'effective striking'}` };
  }
}
export const styleAnalyzer = new StyleAnalyzer();

/** Similarity Engine */
export class SimilarityEngine {
  findSimilar(target: StyleProfile, candidates: { id: string; name: string; profile: StyleProfile }[], limit = 10): SimilarityResult[] {
    return candidates.map((c) => {
      const dot = target.signature.reduce((s, v, i) => s + v * (c.profile.signature[i] || 0), 0);
      const magA = Math.sqrt(target.signature.reduce((s, v) => s + v * v, 0));
      const magB = Math.sqrt(c.profile.signature.reduce((s, v) => s + v * v, 0));
      const similarity = magA > 0 && magB > 0 ? dot / (magA * magB) : 0;
      const sharedStrengths = Object.entries(target.dimensions).filter(([k, v]) => v > 7 && (c.profile.dimensions[k as StyleDimension] || 0) > 7).map(([k]) => k);
      const sharedWeaknesses = Object.entries(target.dimensions).filter(([k, v]) => v < 5 && (c.profile.dimensions[k as StyleDimension] || 0) < 5).map(([k]) => k);
      return { fighterId: c.id, name: c.name, similarity, sharedStrengths, sharedWeaknesses };
    }).sort((a, b) => b.similarity - a.similarity).slice(0, limit);
  }

  computeSimilarity(a: StyleProfile, b: StyleProfile): number {
    const dot = a.signature.reduce((s, v, i) => s + v * (b.signature[i] || 0), 0);
    const mA = Math.sqrt(a.signature.reduce((s, v) => s + v * v, 0));
    const mB = Math.sqrt(b.signature.reduce((s, v) => s + v * v, 0));
    return mA > 0 && mB > 0 ? dot / (mA * mB) : 0;
  }
}
export const similarityEngine = new SimilarityEngine();

/** Career Projection */
export class CareerProjectionEngine {
  project(fighter: { age: number; wins: number; losses: number; recentForm: number[] }): CareerProjection {
    const age = fighter.age;
    const winRate = fighter.wins / Math.max(fighter.wins + fighter.losses, 1);
    const recentWins = fighter.recentForm?.filter((r) => r > 0).length || 0;
    const recentTotal = Math.max(fighter.recentForm?.length || 1, 1);

    let phase: CareerPhase = 'prospect';
    if (fighter.wins > 15) phase = age < 32 ? 'peak' : 'declining';
    else if (fighter.wins > 8) phase = age < 30 ? 'rising' : 'prime';
    else if (fighter.wins > 3) phase = 'rising';

    const trajectory: 'rising' | 'stable' | 'declining' = recentWins / recentTotal > 0.6 ? 'rising' : recentWins / recentTotal < 0.4 ? 'declining' : 'stable';
    return { currentPhase: phase, estimatedPeak: 30, declineAge: 35 + Math.floor(Math.random() * 4), trajectory, titleProbability: winRate > 0.7 ? 0.4 + Math.random() * 0.3 : 0.05 + Math.random() * 0.3, rankingProjection: Array.from({ length: 5 }, (_, i) => Math.max(1, 15 - i * 2 - Math.floor(Math.random() * 3))), longevityYears: 5 + Math.floor(Math.random() * 8) };
  }
}
export const careerProjection = new CareerProjectionEngine();

/** Matchup Analyzer */
export class MatchupAnalyzer {
  analyze(a: StyleProfile, b: StyleProfile): MatchupAnalysis {
    const advantages: string[] = []; const disadvantages: string[] = [];
    for (const dim of Object.keys(a.dimensions) as StyleDimension[]) {
      const diff = (a.dimensions[dim] || 0) - (b.dimensions[dim] || 0);
      if (diff > 2) advantages.push(`${dim} advantage`);
      else if (diff < -2) disadvantages.push(`${dim} disadvantage`);
    }
    return {
      advantages, disadvantages,
      keyExchanges: ['Striking exchanges', 'Clinch battles', 'Ground scrambles'],
      dangerAreas: ['Knee strikes in clinch', 'Guillotine from guard'],
      expectedPace: a.dimensions.pace > 7 ? 'fast' : 'moderate',
      winConditions: ['Control distance', 'Avoid takedowns', 'Target body early'],
      lossConditions: ['Gets taken down repeatedly', 'Gasses in later rounds'],
      overallEdge: advantages.length - disadvantages.length,
    };
  }
}
export const matchupAnalyzer = new MatchupAnalyzer();

/** Scouting Report Generator */
export class ReportGenerator {
  generate(type: ReportType, fighterId: string, fighterName: string, style: StyleProfile, projection: CareerProjection): ScoutingReport {
    const sections = [
      { title: 'Style Overview', content: style.summary },
      { title: 'Career Phase', content: `${projection.currentPhase} — trajectory is ${projection.trajectory}` },
      { title: 'Key Strengths', content: Object.entries(style.dimensions).filter(([, v]) => v > 7).map(([k]) => k).join(', ') },
      { title: 'Projection', content: `Title probability: ${(projection.titleProbability * 100).toFixed(0)}%. Estimated peak age: ${projection.estimatedPeak}.` },
    ];
    return { id: `report-${Date.now()}`, type, fighterId, fighterName, generatedAt: Date.now(), sections, overallGrade: projection.trajectory === 'rising' ? 'A-' : 'B+' };
  }
}
export const reportGenerator = new ReportGenerator();

/** Scouting Analytics */
export class ScoutingAnalytics {
  trackReport(type: ReportType): void {}
  trackComparison(fighterA: string, fighterB: string): void {}
  getMostViewed(): string[] { return []; }
}
export const scoutAnalytics = new ScoutingAnalytics();
