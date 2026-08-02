/** Rankings Components — RankingCard, ChampionCard, DivisionSelector, MovementArrow, etc. */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import { rankingColors } from '../theme';
import type { RankingFighter, RankingMovement } from '../types';

// ── RankingCard ──
export function RankingCard({ rank, previousRank, movement, fighter, subtitle, extra, palette, onPress }: {
  rank: number | null; previousRank?: number | null; movement?: 'up' | 'down' | 'steady' | 'new';
  fighter: RankingFighter; subtitle?: string; extra?: React.ReactNode; palette: any; onPress?: () => void;
}) {
  const moveColor = movement === 'up' ? '#10B981' : movement === 'down' ? '#EF4444' : '#6B7280';
  const moveIcon = movement === 'up' ? '▲' : movement === 'down' ? '▼' : movement === 'new' ? '●' : '—';
  const isTop3 = rank !== null && rank <= 3;

  return (
    <TouchableOpacity onPress={onPress} style={[cs.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}
      accessibilityLabel={`${rank ? `#${rank}` : 'NR'} ${fighter?.fullName || fighter?.lastName}`}>
      <View style={[cs.rankBox, { backgroundColor: isTop3 ? '#F59E0B' : palette.surface.elevated }]}>
        <Text style={[typography.title, { color: isTop3 ? '#FFF' : palette.text.secondary, fontWeight: '700' }]}>
          {fighter?.isChampion ? '👑' : rank ? `#${rank}` : 'NR'}
        </Text>
      </View>
      <View style={{ flex: 1, marginLeft: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{fighter?.fullName || fighter?.lastName || 'Unknown'}</Text>
          <MovementArrow movement={movement ?? 'steady'} previousRank={previousRank ?? rank} rank={rank ?? 0} />
        </View>
        {subtitle && <Text style={[typography.caption, { color: palette.text.secondary }]}>{subtitle}</Text>}
        {fighter?.streak > 0 && (
          <View style={cs.streakBadge}>
            <Text style={[typography.caption, { color: '#10B981', fontWeight: '700' }]}>W{fighter.streak}</Text>
          </View>
        )}
      </View>
      {extra}
    </TouchableOpacity>
  );
}

// ── MovementArrow ──
export function MovementArrow({ movement, previousRank, rank }: { movement: string; previousRank: number | null; rank: number }) {
  if (movement === 'new') return <Text style={[cs.moveText, { color: '#3B82F6' }]}> New</Text>;
  if (movement === 'steady' || !previousRank) return null;
  const diff = previousRank - rank;
  return <Text style={[cs.moveText, { color: diff > 0 ? '#10B981' : diff < 0 ? '#EF4444' : '#6B7280' }]}>{diff > 0 ? ` ▲${diff}` : diff < 0 ? ` ▼${Math.abs(diff)}` : ' —'}</Text>;
}

// ── ChampionCard ──
export function ChampionCard({ fighter, division, defenses, palette }: { fighter: RankingFighter; division: string; defenses: number; palette: any }) {
  return (
    <View style={[cs.champCard, { backgroundColor: '#F59E0B15', borderColor: '#F59E0B30' }]}>
      <View style={[cs.avatar, { backgroundColor: '#F59E0B30' }]}><Text>👑</Text></View>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginTop: 8 }]}>{fighter?.fullName || fighter?.lastName}</Text>
      <Text style={[typography.caption, { color: '#F59E0B', fontWeight: '700' }]}>{division} Champion</Text>
      <Text style={[typography.caption, { color: palette.text.secondary }]}>{defenses} title defenses • {fighter?.record}</Text>
    </View>
  );
}

// ── DivisionSelector ──
export function DivisionSelector({ divisions, selected, onSelect, palette }: { divisions: string[]; selected: string; onSelect: (d: string) => void; palette: any }) {
  return (
    <View style={cs.chipRow}>
      {divisions.map((d) => (
        <TouchableOpacity key={d} onPress={() => onSelect(d)} style={[cs.chip, { backgroundColor: selected === d ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
          <Text style={[typography.bodySmall, { color: selected === d ? '#FFF' : palette.text.secondary }]}>{d}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

// ── RankBadge ──
export function RankBadge({ rank, size = 40 }: { rank: number | null; size?: number }) {
  return (
    <View style={[cs.rankBox, { width: size, height: size, borderRadius: size / 2 }]}>
      <Text style={{ color: '#FFF', fontWeight: '700', fontSize: size / 3 }}>{rank ? `#${rank}` : 'NR'}</Text>
    </View>
  );
}

// ── StreakBadge ──
export function StreakBadge({ streak }: { streak: number }) {
  return <Text style={[cs.moveText, { color: streak > 0 ? '#10B981' : '#EF4444' }]}>{streak > 0 ? `W${streak}` : `L${Math.abs(streak)}`}</Text>;
}

// ── EloBadge ──
export function EloBadge({ elo }: { elo: number | null }) {
  if (!elo) return null;
  return <View style={[cs.badge, { backgroundColor: '#3B82F620' }]}><Text style={[cs.mono, { color: '#3B82F6', fontWeight: '700' }]}>{Math.round(elo)}</Text></View>;
}

// ── CompositeBadge ──
export function CompositeBadge({ score }: { score: number | null }) {
  if (!score) return null;
  return <View style={[cs.badge, { backgroundColor: '#8B5CF620' }]}><Text style={[cs.mono, { color: '#8B5CF6', fontWeight: '700' }]}>{score.toFixed(1)}</Text></View>;
}

// ── Skeletons ──
export function RankingsSkeleton() {
  return <View style={{ padding: spacing.lg }}>{[1,2,3,4,5,6,7,8].map((i) => <View key={i} style={[cs.skel, { backgroundColor: '#1A1A2E' }]} />)}</View>;
}

export function RankingEmpty({ message, palette }: { message: string; palette?: any }) {
  return <View style={cs.empty}><Text style={{ color: '#9CA3AF' }}>{message}</Text></View>;
}

export function RankingError({ onRetry }: { onRetry: () => void }) {
  return (
    <View style={cs.empty}>
      <Text style={{ fontSize: 40 }}>⚠️</Text>
      <Text style={{ color: '#9CA3AF', marginTop: 8 }}>Couldn't load rankings</Text>
      <TouchableOpacity onPress={onRetry} style={{ marginTop: 16, padding: 12, backgroundColor: '#3B82F6', borderRadius: 8 }}>
        <Text style={{ color: '#FFF' }}>Retry</Text>
      </TouchableOpacity>
    </View>
  );
}

const cs = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 4, borderRadius: radius.md, borderWidth: 0.5 },
  rankBox: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#1E1E32' },
  moveText: { fontSize: 12, fontWeight: '700', marginLeft: 4 },
  streakBadge: { alignSelf: 'flex-start', marginTop: 2 },
  champCard: { alignItems: 'center', padding: spacing.xl, margin: spacing.lg, borderRadius: radius.lg, borderWidth: 1 },
  avatar: { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', padding: spacing.md, gap: 6 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, alignSelf: 'flex-start' },
  mono: { fontFamily: 'monospace', fontSize: 13 },
  skel: { height: 64, borderRadius: radius.md, marginBottom: 8 },
  empty: { alignItems: 'center', paddingVertical: 60 },
});
