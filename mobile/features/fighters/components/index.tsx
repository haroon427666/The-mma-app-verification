/** Fighters Components — one file per component group */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import type { FighterProfile, FighterStats as FStats, StyleAnalysis, SimilarFighter, FightHistoryEntry } from '../types';

// ── FighterHeader ──
export function FighterHeader({ fighter, palette }: { fighter: FighterProfile; palette: any }) {
  return (
    <View style={cs.banner}>
      <View style={[cs.avatarLg, { backgroundColor: palette.surface.elevated }]}><Text style={{ fontSize: 40 }}>🥊</Text></View>
      <Text style={[typography.headline, { color: palette.text.primary, marginTop: 12, textAlign: 'center' }]}>{fighter.fullName || `${fighter.firstName} ${fighter.lastName}`}</Text>
      {fighter.nickname && <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center' }]}>"{fighter.nickname}"</Text>}
      <View style={cs.metaRow}>
        {fighter.isChampion && <View style={[cs.badge, { backgroundColor: '#F59E0B' }]}><Text style={cs.badgeText}>👑 Champion</Text></View>}
        {fighter.latestRank && !fighter.isChampion && <Text style={[typography.body, { color: '#F59E0B' }]}>#{fighter.latestRank} {fighter.weightClass}</Text>}
      </View>
    </View>
  );
}

// ── FighterRecord ──
export function FighterRecord({ fighter, palette }: { fighter: FighterProfile; palette: any }) {
  const record = `${fighter.wins}-${fighter.losses}${fighter.draws ? `-${fighter.draws}` : ''}`;
  const finishRate = fighter.wins > 0 ? Math.round((fighter.koWins + fighter.subWins) / fighter.wins * 100) : 0;
  return (
    <View style={cs.grid}>
      <StatBox label="Record" value={record} palette={palette} />
      <StatBox label="Finish Rate" value={`${finishRate}%`} palette={palette} />
      <StatBox label="Elo" value={fighter.eloRating ? String(Math.round(fighter.eloRating)) : '--'} palette={palette} />
      <StatBox label="Streak" value={fighter.streak > 0 ? `W${fighter.streak}` : fighter.streak < 0 ? `L${Math.abs(fighter.streak)}` : '--'} palette={palette} />
    </View>
  );
}

function StatBox({ label, value, palette }: { label: string; value: string; palette: any }) {
  return (
    <View style={[cs.statBox, { backgroundColor: palette.surface.elevated }]}>
      <Text style={[typography.title, { color: palette.text.primary, fontWeight: '700' }]}>{value}</Text>
      <Text style={[typography.caption, { color: palette.text.tertiary }]}>{label}</Text>
    </View>
  );
}

// ── FighterStats ──
export function FighterStats({ stats, fighter, palette }: { stats: FStats; fighter: FighterProfile; palette: any }) {
  return (
    <View style={cs.section}>
      <SectionTitle title="Striking" palette={palette} />
      <StatRow label="Sig. Strikes/min" value={stats.sigStrikesLandedPerMin?.toFixed(1)} palette={palette} />
      <StatRow label="Accuracy" value={`${stats.sigStrikesAccuracyPct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="Defense" value={`${stats.sigStrikesDefensePct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="Knockdowns" value={`${stats.knockdownsTotal ?? 0}`} palette={palette} />
      <SectionTitle title="Grappling" palette={palette} />
      <StatRow label="Takedowns/15" value={stats.takedownAvgPer15?.toFixed(1)} palette={palette} />
      <StatRow label="TD Accuracy" value={`${stats.takedownAccuracyPct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="TD Defense" value={`${stats.takedownDefensePct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="Subs/15" value={stats.submissionAvgPer15?.toFixed(1)} palette={palette} />
    </View>
  );
}

function SectionTitle({ title, palette }: { title: string; palette: any }) {
  return <Text style={[typography.subtitle, { color: palette.text.primary, marginTop: 20, marginBottom: 8 }]}>{title}</Text>;
}

function StatRow({ label, value, palette }: { label: string; value: string; palette: any }) {
  return (
    <View style={cs.statRow}>
      <Text style={[typography.body, { color: palette.text.secondary }]}>{label}</Text>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{value || '--'}</Text>
    </View>
  );
}

// ── FightHistoryRow ──
export function FightHistoryRow({ fight, palette }: { fight: FightHistoryEntry; palette: any }) {
  const won = fight.result === 'W';
  return (
    <View style={[cs.historyRow, { borderLeftColor: won ? '#10B981' : '#EF4444', backgroundColor: palette.surface.card }]}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]}>{fight.opponent?.name}</Text>
        <Text style={[typography.caption, { color: won ? '#10B981' : '#EF4444', fontWeight: '700' }]}>{fight.result} {fight.method} R{fight.round}</Text>
      </View>
      <Text style={[typography.caption, { color: palette.text.tertiary }]}>{fight.eventName} • {fight.date?.slice(0, 10)}</Text>
    </View>
  );
}

// ── SimilarityCard ──
export function SimilarityCard({ item, palette }: { item: SimilarFighter; palette: any }) {
  return (
    <TouchableOpacity style={[cs.simCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.fighter.fullName || item.fighter.lastName}</Text>
        <View style={[cs.simScore, { backgroundColor: palette.primary[500] }]}>
          <Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{Math.round(item.similarityScore * 100)}%</Text>
        </View>
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
        {item.breakdown?.filter((b) => b.verdict === 'similar').slice(0, 3).map((b, i) => (
          <View key={i} style={[cs.traitPill, { backgroundColor: palette.surface.elevated }]}>
            <Text style={[typography.caption, { color: palette.text.secondary }]}>{b.trait}</Text>
          </View>
        ))}
      </View>
    </TouchableOpacity>
  );
}

// ── FighterStyleBadge ──
export function FighterStyleBadge({ style, palette }: { style: StyleAnalysis; palette: any }) {
  return (
    <View style={[cs.styleCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <Text style={[typography.bodySmall, { color: palette.primary[400], textTransform: 'uppercase' }]}>{style.primaryStyle}</Text>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{style.archetype}</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
        {style.strengths?.slice(0, 4).map((s, i) => (
          <View key={i} style={[cs.traitPill, { backgroundColor: '#10B98120' }]}><Text style={[typography.caption, { color: '#10B981' }]}>+{s}</Text></View>
        ))}
      </View>
    </View>
  );
}

// ── Other ──
export function RankMovement({ rank, previous }: { rank: number; previous: number }) {
  const diff = previous - rank;
  return <Text style={[typography.caption, { color: diff > 0 ? '#10B981' : diff < 0 ? '#EF4444' : '#9CA3AF', fontWeight: '700' }]}>{diff > 0 ? `▲${diff}` : diff < 0 ? `▼${Math.abs(diff)}` : '—'}</Text>;
}

export function FavoriteButton({ isFav, onToggle, palette }: { isFav: boolean; onToggle: () => void; palette: any }) {
  return (
    <TouchableOpacity onPress={onToggle} style={[cs.favBtn, { backgroundColor: isFav ? '#EF4444' : palette.surface.card, borderColor: isFav ? '#EF4444' : palette.surface.border }]}>
      <Text style={[typography.bodySmall, { color: isFav ? '#FFF' : palette.text.primary }]}>{isFav ? '❤️ Favorited' : '♡ Favorite'}</Text>
    </TouchableOpacity>
  );
}

export { FighterCardSkeleton, ProfileSkeleton } from './Skeletons';
export { EmptyState, ErrorState } from './ErrorStates';

const cs = StyleSheet.create({
  banner: { padding: spacing.xl, alignItems: 'center', backgroundColor: '#1A1A2E' },
  avatarLg: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center' },
  metaRow: { flexDirection: 'row', gap: 8, marginTop: 8 },
  badge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  badgeText: { color: '#FFF', fontSize: 12, fontWeight: '700' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', padding: spacing.lg, gap: 8 },
  statBox: { padding: spacing.md, borderRadius: radius.md, alignItems: 'center', minWidth: 80 },
  section: { paddingHorizontal: spacing.lg },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  historyRow: { borderLeftWidth: 3, padding: spacing.md, borderRadius: radius.sm, marginBottom: 8, marginHorizontal: spacing.lg },
  simCard: { padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 8 },
  simScore: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  traitPill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  styleCard: { padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5, marginBottom: spacing.lg },
  favBtn: { flex: 1, paddingVertical: 12, borderRadius: radius.md, borderWidth: 1, alignItems: 'center' },
});
