/** Fighter Scouting — hooks + index */
import { useState, useCallback } from 'react';
import { styleAnalyzer, similarityEngine, careerProjection, matchupAnalyzer, reportGenerator, scoutAnalytics } from './ScoutingEngine';
import type { StyleProfile, SimilarityResult, CareerProjection, MatchupAnalysis, ScoutingReport, ReportType } from './ScoutingEngine';

export function useStyleAnalysis() {
  const [profile, setProfile] = useState<StyleProfile | null>(null);
  const analyze = useCallback((fighter: { stats: Record<string, number>; record: { koWins: number; subWins: number; decWins: number; wins: number } }) => {
    const p = styleAnalyzer.analyze(fighter); setProfile(p); return p;
  }, []);
  return { profile, analyze };
}

export function useSimilarity(target: StyleProfile | null, candidates: { id: string; name: string; profile: StyleProfile }[]) {
  const [results, setResults] = useState<SimilarityResult[]>([]);
  const find = useCallback(() => { if (target) setResults(similarityEngine.findSimilar(target, candidates)); }, [target, candidates]);
  return { results, find };
}

export function useCareerProjection() {
  return { project: (fighter: { age: number; wins: number; losses: number; recentForm: number[] }) => careerProjection.project(fighter) };
}

export function useMatchupAnalysis() {
  const [analysis, setAnalysis] = useState<MatchupAnalysis | null>(null);
  const analyze = useCallback((a: StyleProfile, b: StyleProfile) => { const result = matchupAnalyzer.analyze(a, b); setAnalysis(result); return result; }, []);
  return { analysis, analyze };
}

export function useScoutingReport() {
  const [report, setReport] = useState<ScoutingReport | null>(null);
  const [loading, setLoading] = useState(false);
  const generate = useCallback(async (type: ReportType, fighterId: string, fighterName: string, style: StyleProfile, projection: CareerProjection) => {
    setLoading(true); try { const r = reportGenerator.generate(type, fighterId, fighterName, style, projection); setReport(r); return r; } finally { setLoading(false); }
  }, []);
  return { report, generate, loading };
}

/*
## Fighter Scouting Platform

### Style Dimensions (12)
| Dimension | Range | Description |
|---|---|---|
| striking | 1-10 | Standup effectiveness |
| grappling | 1-10 | Ground control |
| wrestling | 1-10 | Takedown ability |
| bjj | 1-10 | Submission threat |
| cardio | 1-10 | Gas tank |
| fight_iq | 1-10 | Decision making |
| aggression | 1-10 | Forward pressure |
| defense | 1-10 | Damage avoidance |
| counter_striking | 1-10 | Counter ability |
| scrambling | 1-10 | Scramble wins |
| clinch | 1-10 | Close range |
| pace | 1-10 | Output volume |

### Similarity
- Cosine similarity on 12-dim style vectors
- Shared strengths (both >7)
- Shared weaknesses (both <5)

### Career Phases
prospect → rising → prime → peak → declining → veteran

### Hooks
- useStyleAnalysis() → analyze fighter style
- useSimilarity() → find similar fighters
- useCareerProjection() → project career trajectory
- useMatchupAnalysis() → head-to-head breakdown
- useScoutingReport() → generate full reports
*/

export { styleAnalyzer, similarityEngine, careerProjection, matchupAnalyzer, reportGenerator, scoutAnalytics } from './ScoutingEngine';
export type { FightingStyle, StyleDimension, CareerPhase, ReportType, StyleProfile, SimilarityResult, CareerProjection, MatchupAnalysis, ScoutingReport } from './ScoutingEngine';
